# core/views.py
import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from .models import SocialAccount, Content, PublishedPost, UserSettings
from .forms import ContentForm, SettingsForm
from .agents.adaptation import adapt_content
from .agents.publisher import publish_content, publish_scheduled_posts
import requests
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

# Set up logging
logger = logging.getLogger(__name__)

@login_required
def dashboard(request):
    """Dashboard with engagement metrics and upcoming posts"""
    try:
        # Get current date information
        from datetime import datetime, timedelta
        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)
        
        # Check if user has connected any platforms
        has_platforms = SocialAccount.objects.filter(user=request.user).exists()
        if not has_platforms:
            messages.info(request, "Connect your social media accounts to get started!")
            
        # Get upcoming content (next 7 days)
        upcoming_content = Content.objects.filter(
            user=request.user,
            scheduled_time__gte=timezone.now(),
            scheduled_time__lte=timezone.now() + timezone.timedelta(days=7),
            is_draft=False
        ).order_by('scheduled_time')[:5]
        
        # Get saved drafts
        drafts = Content.objects.filter(
            user=request.user,
            is_draft=True
        ).order_by('-created_at')[:3]
        
        # Calculate stats
        total_posts = Content.objects.filter(user=request.user, is_draft=False).count()
        published_posts = PublishedPost.objects.filter(
            content__user=request.user,
            published_at__isnull=False
        )
        
        # Calculate new posts this week
        week_ago = timezone.now() - timedelta(days=7)
        new_posts_this_week = Content.objects.filter(
            user=request.user,
            created_at__gte=week_ago,
            is_draft=False
        ).count()
        
        # Calculate engagement metrics
        engagement_data = {
            'likes': 0,
            'shares': 0,
            'comments': 0
        }
        
        for post in published_posts:
            metrics = post.metrics or {}
            engagement_data['likes'] += metrics.get('likes', 0)
            engagement_data['shares'] += metrics.get('shares', 0)
            engagement_data['comments'] += metrics.get('comments', 0)
        
        # Calculate engagement rate (simplified formula)
        total_engagement = engagement_data['likes'] + engagement_data['shares'] * 2 + engagement_data['comments'] * 3
        follower_count = request.user.socialaccount_set.count() * 100  # Simulated follower count
        engagement_rate = (total_engagement / (follower_count or 1)) * 100 if published_posts.count() > 0 else 0
        
        # Calculate engagement rate change (simulated)
        engagement_rate_change = 5.2  # Simulated positive change
        
        # Get connected accounts as objects, not dictionaries
        connected_accounts = SocialAccount.objects.filter(user=request.user)
        
        # Get posts with errors
        error_posts = PublishedPost.objects.filter(
            content__user=request.user,
            published_at__isnull=False
        ).exclude(metrics__error__isnull=True)
        
        context = {
            'today': timezone.now(),
            'tomorrow': timezone.now() + timedelta(days=1),
            'upcoming_content': upcoming_content,
            'drafts': drafts,
            'total_posts': total_posts,
            'new_posts_this_week': new_posts_this_week,
            'engagement_rate': round(engagement_rate, 1),
            'engagement_rate_change': engagement_rate_change,
            'connected_accounts': connected_accounts,
            'engagement_data': engagement_data,
            'recent_posts': published_posts.order_by('-published_at')[:3],
            'error_posts': error_posts,
            'has_platforms': has_platforms
        }
        return render(request, 'core/dashboard.html', context)
    
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        messages.error(request, "Couldn't load dashboard data. Please try again.")
        return render(request, 'core/dashboard.html')

@login_required
def create(request):
    """Content creation with real-time preview"""
    try:
        # Get user's connected social media accounts
        connected_accounts = SocialAccount.objects.filter(user=request.user)
        
        # Always show all platform choices, even if not connected
        # This ensures we always have 6 platforms available
        platform_choices = list(SocialAccount.PLATFORM_CHOICES)
        
        # Check if user has any connected platforms
        has_platforms = connected_accounts.exists()
        
        # Check if we're editing a draft
        draft_id = request.GET.get('draft_id')
        draft = None
        if draft_id:
            try:
                draft = Content.objects.get(id=draft_id, user=request.user, is_draft=True)
            except Content.DoesNotExist:
                messages.error(request, "Draft not found or you don't have permission to edit it.")
        
        if request.method == 'POST':
            form = ContentForm(request.POST, request.FILES, instance=draft)
            
            # Always set platform choices to all available platforms
            form.fields['platforms'].choices = platform_choices
            
            if form.is_valid():
                content = form.save(commit=False)
                content.user = request.user
                
                # Save platforms selection if available
                if 'platforms' in form.cleaned_data:
                    content.platforms = form.cleaned_data['platforms']
                else:
                    content.platforms = []
                
                # If this was a draft, mark it as not a draft anymore
                if draft:
                    content.is_draft = False
                
                content.save()
                
                # Create message if no platforms are connected
                if not has_platforms:
                    messages.success(request, "Content saved successfully!")
                    messages.info(request, "Connect social media accounts to publish your content.")
                    return redirect('dashboard')
                
                # Process for each selected platform
                created_posts = []
                adaptation_errors = []
                
                # First verify all platforms have been adapted
                for platform in content.platforms:
                    try:
                        # Use adaptation agent to format content (this should already be adapted in the preview step)
                        # This is a safety check to ensure content is always adapted before publishing
                        adapted_text = adapt_content(
                            content.original_text, 
                            platform,
                            content.tone
                        )
                        
                        if not adapted_text or not adapted_text.strip():
                            error_msg = f"Failed to adapt content for {dict(SocialAccount.PLATFORM_CHOICES).get(platform, platform)}"
                            adaptation_errors.append(error_msg)
                            logger.error(error_msg)
                            continue
                        
                        # Create scheduled post
                        post = PublishedPost.objects.create(
                            content=content,
                            platform=platform,
                            adapted_text=adapted_text,
                            scheduled_time=content.scheduled_time
                        )
                        created_posts.append(post)
                        logger.info(f"Created post for platform {platform} scheduled at {content.scheduled_time}")
                    except Exception as e:
                        error_msg = f"Error creating post for platform {platform}: {str(e)}"
                        adaptation_errors.append(error_msg)
                        logger.error(error_msg)
                        messages.error(request, f"Error processing content for {dict(SocialAccount.PLATFORM_CHOICES).get(platform, platform)}")
                
                # Handle success or failure
                if created_posts:
                    # Check if posts should be published immediately
                    if timezone.now() >= content.scheduled_time:
                        from .agents.publisher import publish_scheduled_posts
                        publish_count = publish_scheduled_posts()
                        messages.success(request, f"Content created and published successfully to {len(created_posts)} platform(s)!")
                        
                        if adaptation_errors:
                            messages.warning(request, f"Some platforms encountered errors: {', '.join(adaptation_errors)}")
                    else:
                        scheduled_date = content.scheduled_time.strftime('%b %d, %Y at %I:%M %p')
                        messages.success(request, f"Content scheduled successfully for {scheduled_date}!")
                        
                        if adaptation_errors:
                            messages.warning(request, f"Some platforms encountered errors: {', '.join(adaptation_errors)}")
                else:
                    messages.error(request, "Failed to create content for any platforms.")
                
                return redirect('dashboard')
            else:
                messages.error(request, "Please correct the errors below.")
        else:
            # GET request - create new form or load draft
            if draft:
                form = ContentForm(instance=draft)
                messages.info(request, "You're editing a draft. When you're done, click 'Adapt & Schedule' to publish.")
            else:
                form = ContentForm()
            
            # Always set all platforms as choices
            form.fields['platforms'].choices = platform_choices
            
            if not has_platforms:
                messages.info(request, "You haven't connected any social media accounts yet. Your content can't be published until you connect at least one account.")
        
        # Get user's tone preference for default selection
        try:
            user_settings = UserSettings.objects.get(user=request.user)
            default_tone = user_settings.tone_preference
        except UserSettings.DoesNotExist:
            default_tone = 'professional'
        
        context = {
            'form': form,
            'platform_choices': platform_choices,
            'default_tone': default_tone,
            'has_platforms': has_platforms,
            'preview_data': json.dumps({}),  # Empty preview for initial load
            'editing_draft': draft is not None
        }
        return render(request, 'core/create.html', context)
    
    except Exception as e:
        logger.error(f"Content creation error: {str(e)}")
        messages.error(request, "Failed to create content. Please try again.")
        return redirect('create')
@login_required
def generate_preview(request):
    """AJAX endpoint for generating AI-adapted content previews"""
    if request.method == 'POST':
        try:
            # Get form data - handle both AJAX and regular form submissions
            text = request.POST.get('text', '') or request.POST.get('original_text', '')
            tone = request.POST.get('tone', 'professional')
            
            # Handle platforms array - try different parameter formats
            platforms = (request.POST.getlist('platforms[]') or 
                        request.POST.getlist('platforms') or 
                        [])
            
            logger.info(f"=== PREVIEW GENERATION REQUEST ===")
            logger.info(f"User: {request.user.username}")
            logger.info(f"Text length: {len(text)} characters")
            logger.info(f"Tone: {tone}")
            logger.info(f"Platforms: {platforms}")
            
            # Validate 
            if not text or not text.strip():
                logger.warning("Empty text provided for preview generation")
                return JsonResponse({
                    'status': 'error',
                    'message': 'No content provided.'
                })
            
            if not platforms:
                logger.info("No platforms specified, using all available platforms")
                # If no specific platforms, generate for all
                platforms = ['TW', 'FB', 'IG', 'LI', 'TT', 'YT']
            
            # Generate previews for each platform
            previews = {}
            errors = {}
            successful_platforms = []
            
            # Generate simple AI suggestions based on content
            suggestions = []
            content_length = len(text)
            
            if content_length < 50:
                suggestions.append("Consider adding more detail to make your content more engaging")
            elif content_length > 280:
                suggestions.append("Consider shortening your content for better engagement on platforms like X")
            
            if not any(char in text for char in ['!', '?', '💡', '🚀', '✨']):
                suggestions.append("Add some excitement with emojis or exclamation points!")
            
            if '#' not in text:
                suggestions.append("Consider adding relevant hashtags to increase discoverability")
            
            if 'http' not in text.lower() and 'www' not in text.lower():
                suggestions.append("Include a call-to-action or link to drive traffic")
            
            # Select one random suggestion if any exist
            ai_suggestion = ""
            if suggestions:
                import random
                ai_suggestion = random.choice(suggestions)
            
            # Track overall processing time for metrics
            import time
            start_time = time.time()
            
            # Platform-specific metadata
            platform_metadata = {
                "TW": {"char_limit": 280, "name": "X"},
                "FB": {"char_limit": 5000, "name": "Facebook"},
                "IG": {"char_limit": 2200, "name": "Instagram"},
                "LI": {"char_limit": 3000, "name": "LinkedIn"},
                "TT": {"char_limit": 2200, "name": "TikTok"},
                "YT": {"char_limit": 5000, "name": "YouTube"}
            }
            
            for platform in platforms:
                try:
                    logger.info(f"Generating preview for platform: {platform}")
                    platform_start = time.time()
                    
                    # Platform validation
                    if platform not in platform_metadata:
                        error_msg = f"Unknown platform: {platform}"
                        errors[platform] = error_msg
                        logger.error(error_msg)
                        continue
                    
                    # Call adaptation service
                    adapted_text = adapt_content(text, platform, tone)
                    platform_time = time.time() - platform_start
                    
                    # Validate result
                    if adapted_text and len(adapted_text.strip()) > 0:
                        # Check character limits and warn if exceeded
                        char_limit = platform_metadata[platform]["char_limit"]
                        if len(adapted_text) > char_limit:
                            logger.warning(f"Adapted text for {platform} exceeds character limit: {len(adapted_text)}/{char_limit}")
                            # We'll still use it but notify the user
                            errors[f"{platform}_warning"] = f"Text exceeds {platform_metadata[platform]['name']} character limit"
                        
                        previews[platform] = adapted_text
                        successful_platforms.append(platform)
                        logger.info(f"Successfully generated preview for {platform} in {platform_time:.2f}s")
                    else:
                        error_msg = f"Empty result for {platform}"
                        errors[platform] = error_msg
                        logger.error(error_msg)
                        
                except Exception as platform_error:
                    error_msg = f"Error generating preview for {platform}: {str(platform_error)}"
                    errors[platform] = error_msg
                    logger.error(error_msg)
            
            # Determine response status
            if successful_platforms:
                # Overall processing metrics
                total_time = time.time() - start_time
                logger.info(f"Preview generation completed in {total_time:.2f}s. Success: {successful_platforms}, Errors: {list(errors.keys())}")
                
                response_data = {
                    'status': 'success',
                    'previews': previews,
                    'errors': errors,
                    'successful_platforms': successful_platforms,
                    'original_text': text,
                    'tone': tone,
                    'processing_time': f"{total_time:.2f}s"
                }
                
                # Add suggestions if any were generated
                if ai_suggestion:
                    response_data['suggestions'] = ai_suggestion
                
                return JsonResponse(response_data)
            else:
                logger.error("No previews generated successfully")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Failed to generate any previews',
                    'errors': errors
                })
                
        except Exception as e:
            logger.error(f"Preview generation error: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'Failed to generate preview: {str(e)}'
            })
    
    logger.warning("Invalid request method for generate_preview endpoint")
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def analytics(request):
    """Analytics dashboard with engagement metrics"""
    try:
        # Get published posts with engagement metrics
        published_posts = PublishedPost.objects.filter(
            content__user=request.user
        ).order_by('-published_at')
        
        # Calculate summary metrics
        summary = {
            'likes': 0,
            'shares': 0,
            'comments': 0,
            'posts': published_posts.count(),
            'positive': 0,
            'neutral': 0,
            'negative': 0
        }
        
        # Engagement data for charts
        engagement_timeline = []
        platform_engagement = {p[0]: {'likes': 0, 'shares': 0, 'comments': 0} 
                              for p in SocialAccount.PLATFORM_CHOICES}
        
        for post in published_posts:
            # Summary metrics
            summary['likes'] += post.metrics.get('likes', 0)
            summary['shares'] += post.metrics.get('shares', 0)
            summary['comments'] += post.metrics.get('comments', 0)
            
            # Sentiment analysis
            sentiment = post.metrics.get('sentiment', 0.7)
            if sentiment > 0.6:
                summary['positive'] += 1
            elif sentiment > 0.4:
                summary['neutral'] += 1
            else:
                summary['negative'] += 1
            
            # Timeline data (weekly buckets)
            week = post.published_at.isocalendar()[1]
            if not engagement_timeline or engagement_timeline[-1]['week'] != week:
                engagement_timeline.append({
                    'week': week,
                    'likes': post.metrics.get('likes', 0),
                    'shares': post.metrics.get('shares', 0),
                    'comments': post.metrics.get('comments', 0)
                })
            else:
                engagement_timeline[-1]['likes'] += post.metrics.get('likes', 0)
                engagement_timeline[-1]['shares'] += post.metrics.get('shares', 0)
                engagement_timeline[-1]['comments'] += post.metrics.get('comments', 0)
            
            # Platform engagement
            platform_key = post.platform
            if platform_key in platform_engagement:
                platform_engagement[platform_key]['likes'] += post.metrics.get('likes', 0)
                platform_engagement[platform_key]['shares'] += post.metrics.get('shares', 0)
                platform_engagement[platform_key]['comments'] += post.metrics.get('comments', 0)
        
        # Calculate percentages
        total_sentiment = summary['positive'] + summary['neutral'] + summary['negative']
        if total_sentiment > 0:
            summary['positive_pct'] = round(summary['positive'] / total_sentiment * 100)
            summary['neutral_pct'] = round(summary['neutral'] / total_sentiment * 100)
            summary['negative_pct'] = round(summary['negative'] / total_sentiment * 100)
        else:
            summary['positive_pct'] = summary['neutral_pct'] = summary['negative_pct'] = 0
        
        context = {
            'published_posts': published_posts[:10],  # Top 10 for table
            'summary': summary,
            'engagement_timeline': engagement_timeline[-8:],  # Last 8 weeks
            'platform_engagement': platform_engagement,
            'top_posts': published_posts.order_by('-metrics__likes')[:5]
        }
        return render(request, 'core/analytics.html', context)
    
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        messages.error(request, "Couldn't load analytics data. Please try again.")
        return render(request, 'core/analytics.html')

@login_required
def all_posts(request):
    """View all scheduled and published posts"""
    try:
        # Get all content and published posts
        content_posts = Content.objects.filter(user=request.user, is_draft=False).order_by('-scheduled_time')
        
        # Get drafts
        drafts = Content.objects.filter(user=request.user, is_draft=True).order_by('-created_at')
        
        # Get published posts with status information
        published_posts = PublishedPost.objects.filter(
            content__user=request.user
        ).select_related('content').order_by('-scheduled_time')
        
        # Organize published posts by status
        scheduled_posts = []
        successful_posts = []
        failed_posts = []
        
        for post in published_posts:
            if post.published_at is None:
                # Not yet published
                scheduled_posts.append(post)
            elif post.metrics and 'error' in post.metrics:
                # Published with error
                failed_posts.append(post)
            else:
                # Successfully published
                successful_posts.append(post)
        
        context = {
            'content_posts': content_posts,
            'drafts': drafts,
            'scheduled_posts': scheduled_posts,
            'successful_posts': successful_posts,
            'failed_posts': failed_posts,
            'total_drafts': len(drafts),
            'total_scheduled': len(scheduled_posts),
            'total_successful': len(successful_posts),
            'total_failed': len(failed_posts)
        }
        return render(request, 'core/all_posts.html', context)
    
    except Exception as e:
        logger.error(f"All posts error: {str(e)}")
        messages.error(request, "Couldn't load posts. Please try again.")
        return redirect('dashboard')

@login_required
def post_detail(request, post_id):
    """Detailed view of a specific published post"""
    try:
        post = get_object_or_404(PublishedPost, id=post_id, content__user=request.user)
        
        # Determine post status
        if post.published_at is None:
            status = "scheduled"
            status_message = f"Scheduled for {post.scheduled_time.strftime('%b %d, %Y at %I:%M %p')}"
        elif post.metrics and 'error' in post.metrics:
            status = "failed"
            error = post.metrics['error']
            if isinstance(error, dict) and 'message' in error:
                status_message = f"Failed: {error['message']}"
            else:
                status_message = f"Failed: {error}"
        else:
            status = "published"
            status_message = f"Published on {post.published_at.strftime('%b %d, %Y at %I:%M %p')}"
        
        # For published posts, get metrics summary
        metrics_summary = None
        if status == "published" and post.metrics:
            metrics_summary = {
                'likes': post.metrics.get('likes', 0),
                'shares': post.metrics.get('shares', 0),
                'comments': post.metrics.get('comments', 0),
                'impressions': post.metrics.get('impressions', post.metrics.get('views', 0)),
            }
        
        context = {
            'post': post,
            'status': status,
            'status_message': status_message,
            'metrics_summary': metrics_summary,
            'can_publish': status == "scheduled"
        }
        return render(request, 'core/post_detail.html', context)
    
    except Exception as e:
        logger.error(f"Post detail error: {str(e)}")
        messages.error(request, "Couldn't load post details.")
        return redirect('all_posts')

@login_required
def accounts(request):
    """Account management with connection flows"""
    try:
        connected_accounts = SocialAccount.objects.filter(user=request.user)
        available_platforms = [choice[0] for choice in SocialAccount.PLATFORM_CHOICES]
        
        # Determine which platforms are not connected
        connected_platforms = [acc.platform for acc in connected_accounts]
        unconnected_platforms = [p for p in available_platforms if p not in connected_platforms]
        
        # Check token validity
        account_status = []
        for account in connected_accounts:
            account_status.append({
                'account': account,
                'is_valid': True  # Simulated for now
            })
        
        context = {
            'connected_accounts': account_status,
            'unconnected_platforms': unconnected_platforms,
        }
        return render(request, 'core/accounts.html', context)
    
    except Exception as e:
        logger.error(f"Accounts error: {str(e)}")
        messages.error(request, "Couldn't load account information. Please try again.")
        return redirect('dashboard')

@login_required
def connect_platform(request, platform):
    """Initiate platform connection flow"""
    try:
        # For MVP, we'll simulate the connection
        # In production, this would redirect to OAuth flow
        
        # Check if already connected
        if SocialAccount.objects.filter(user=request.user, platform=platform).exists():
            messages.warning(request, f"You've already connected this platform")
            return redirect('accounts')
        
        # Create placeholder account
        SocialAccount.objects.create(
            user=request.user,
            platform=platform,
            username=f"{request.user.username}_{platform}",
            access_token=f"simulated_token_{platform}_{request.user.id}"
        )
        
        platform_name = dict(SocialAccount.PLATFORM_CHOICES).get(platform, platform)
        messages.success(request, f"{platform_name} connected successfully!")
        return redirect('accounts')
    
    except Exception as e:
        logger.error(f"Platform connection error: {str(e)}")
        platform_name = dict(SocialAccount.PLATFORM_CHOICES).get(platform, platform)
        messages.error(request, f"Failed to connect {platform_name}")
        return redirect('accounts')

@login_required
def disconnect_platform(request, platform_id):
    """Disconnect a platform account"""
    try:
        account = get_object_or_404(SocialAccount, id=platform_id, user=request.user)
        platform_name = account.get_platform_display()
        account.delete()
        messages.success(request, f"{platform_name} disconnected successfully!")
        return redirect('accounts')
    except Exception as e:
        logger.error(f"Disconnection error: {str(e)}")
        messages.error(request, "Failed to disconnect platform")
        return redirect('accounts')

@login_required
def settings(request):
    """User settings with preference management"""
    try:
        user_settings, created = UserSettings.objects.get_or_create(user=request.user)
        
        if request.method == 'POST':
            form = SettingsForm(request.POST, instance=user_settings)
            if form.is_valid():
                form.save()
                messages.success(request, "Settings updated successfully!")
                return redirect('settings')
            else:
                messages.error(request, "Please correct the errors below.")
        else:
            form = SettingsForm(instance=user_settings)
        
        context = {
            'form': form,
        }
        return render(request, 'core/settings.html', context)
    
    except Exception as e:
        logger.error(f"Settings error: {str(e)}")
        messages.error(request, "Couldn't load settings. Please try again.")
        return render(request, 'core/settings.html')

@login_required
def delete_content(request, content_id):
    """Delete scheduled content"""
    try:
        content = get_object_or_404(Content, id=content_id, user=request.user)
        
        # Delete related published posts
        PublishedPost.objects.filter(content=content).delete()
        
        # Delete the content
        content.delete()
        
        messages.success(request, "Content deleted successfully!")
        return redirect('dashboard')
    except Exception as e:
        logger.error(f"Content deletion error: {str(e)}")
        messages.error(request, "Failed to delete content")
        return redirect('dashboard')

@login_required
def publish_now(request, post_id):
    """Publish a post immediately"""
    try:
        post = get_object_or_404(PublishedPost, id=post_id, content__user=request.user)
        
        # Check if already published
        if post.published_at is not None:
            messages.warning(request, "This post has already been published.")
            return redirect('post_detail', post_id=post.id)
        
        # Update scheduled time to now
        post.scheduled_time = timezone.now()
        post.save()
        
        # Publish immediately
        from .agents.publisher import publish_content
        success = publish_content(post)
        
        if success:
            messages.success(request, f"Post successfully published to {post.get_platform_display()}!")
            return redirect('post_detail', post_id=post.id)
        else:
            if post.metrics and 'error' in post.metrics:
                error_message = post.metrics['error']
                if isinstance(error_message, dict) and 'message' in error_message:
                    error_message = error_message['message']
                messages.error(request, f"Failed to publish: {error_message}")
            else:
                messages.error(request, "Failed to publish post. Please check your account connection.")
            
            return redirect('post_detail', post_id=post.id)
    except Exception as e:
        logger.error(f"Publish now error: {str(e)}")
        messages.error(request, "Failed to publish post")
        return redirect('all_posts')

@login_required
def run_scheduler(request):
    """Manual trigger for scheduler (for testing)"""
    try:
        from .agents.publisher import publish_scheduled_posts
        count = publish_scheduled_posts()
        
        if count > 0:
            messages.success(request, f"Scheduler ran successfully! Published {count} posts.")
        else:
            messages.info(request, "Scheduler ran successfully. No posts were due for publishing.")
        
        return redirect('all_posts')
    except Exception as e:
        logger.error(f"Scheduler error: {str(e)}")
        messages.error(request, f"Scheduler encountered an error: {str(e)}")
        return redirect('dashboard')

def signup(request):
    """Handle user registration"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully! Welcome to ChapChap.")
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    
    # Add styling to the form fields
    form.fields['username'].widget.attrs.update({
        'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'
    })
    form.fields['password1'].widget.attrs.update({
        'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'
    })
    form.fields['password2'].widget.attrs.update({
        'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent'
    })
    
    return render(request, 'core/signup.html', {'form': form})

@login_required
def save_draft(request):
    """AJAX endpoint for saving content drafts without navigating away"""
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            # Get form data
            text = request.POST.get('original_text', '')
            tone = request.POST.get('tone', 'professional')
            platforms = request.POST.getlist('platforms', [])
            media = request.FILES.get('media', None)
            
            # Create or update draft
            draft = Content.objects.create(
                user=request.user,
                original_text=text,
                platforms=platforms,
                tone=tone,
                is_draft=True
            )
            
            if media:
                draft.media = media
                draft.save()
            
            return JsonResponse({
                'status': 'success', 
                'message': 'Draft saved successfully!',
                'draft_id': draft.id
            })
        except Exception as e:
            logger.error(f"Draft saving error: {str(e)}")
            return JsonResponse({
                'status': 'error', 
                'message': 'Failed to save draft. Please try again.'
            })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
def refresh_account(request, account_id):
    """Refresh a social media account's status and tokens"""
    try:
        account = get_object_or_404(SocialAccount, id=account_id, user=request.user)
        
        # In a real implementation, this would refresh OAuth tokens, check account status, etc.
        # For demo purposes, we'll just update the connected_at timestamp
        account.connected_at = timezone.now()
        account.save()
        
        messages.success(request, f"{account.get_platform_display()} account refreshed successfully!")
        return redirect('accounts')
    except Exception as e:
        logger.error(f"Account refresh error: {str(e)}")
        messages.error(request, "Failed to refresh account")
        return redirect('accounts')