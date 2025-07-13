import os
import re
import requests
import logging
import random
from django.conf import settings

# Set up logging
logger = logging.getLogger(__name__)

# =============================================================================
# AI MODELS DISABLED FOR DEMO - Using Mock Implementation
# =============================================================================
# This version provides realistic dummy responses without requiring external AI services
# All AI model imports and network calls are commented out for reliability

# # Conditionally import transformers and openai
# try:
#     from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
#     # Initialize Hugging Face pipelines
#     summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
#     classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
#     
#     # Load language model from Hugging Face directly
#     try:
#         llm_model_name = os.getenv("AI_MODEL_TEXT_GENERATION", "microsoft/phi-2")
#         # Initialize tokenizer
#         huggingface_token = os.getenv("HUGGINGFACE_API_KEY", None)
#         # Initialize tokenizer with auth token
#         llm_tokenizer = AutoTokenizer.from_pretrained(
#             llm_model_name, 
#             token=huggingface_token
#         )
#         llm_model = None  # Will be loaded on first use to save memory
#         logger.info(f"Tokenizer loaded from {llm_model_name}")
#         LLM_AVAILABLE = True
#     except Exception as e:
#         logger.warning(f"Could not load language model: {e}")
#         LLM_AVAILABLE = False
#         
#     TRANSFORMERS_AVAILABLE = True
# except ImportError:
#     logger.warning("Transformers package not available, using fallback options")
#     TRANSFORMERS_AVAILABLE = False
#     LLM_AVAILABLE = False

# try:
#     import openai
#     OPENAI_AVAILABLE = True
# except ImportError:
#     logger.warning("OpenAI package not available, using fallback options")
#     OPENAI_AVAILABLE = False

# # Configure OpenRouter (free alternative to OpenAI)
# OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "your_openrouter_key")
# openrouter_url = "https://openrouter.ai/api/v1/chat/completions"

# Mock flags for demo mode
TRANSFORMERS_AVAILABLE = False
LLM_AVAILABLE = False
OPENAI_AVAILABLE = False
logger.info("=== DEMO MODE: Using mock AI responses ===")

# Demo content templates for realistic responses
DEMO_TEMPLATES = {
    "business_casual": [
        "Exciting news from our team! {}",
        "We're thrilled to share: {}",
        "Check out what we've been working on: {}",
        "Here's something that caught our attention: {}",
        "Just wanted to share this update: {}",
        "Something cool happening: {}"
    ],
    "business_professional": [
        "We are pleased to announce: {}",
        "Our latest insights reveal: {}",
        "Industry update: {}",
        "Professional perspective: {}",
        "Strategic analysis shows: {}",
        "Market research indicates: {}"
    ],
    "business_enthusiastic": [
        "🚀 Amazing news! {}",
        "This is HUGE! {}",
        "We can't contain our excitement: {}",
        "Breakthrough alert! {}",
        "Game-changing update: {}",
        "Incredible milestone: {}"
    ],
    "general_casual": [
        "Hey everyone! {}",
        "Just sharing: {}",
        "Thought you'd find this interesting: {}",
        "Quick update: {}",
        "Something worth sharing: {}"
    ],
    "general_professional": [
        "Important update: {}",
        "Key insight: {}",
        "Notable development: {}",
        "Significant information: {}",
        "Essential knowledge: {}"
    ],
    "general_enthusiastic": [
        "Amazing! {}",
        "Incredible news! {}",
        "This is fantastic: {}",
        "Wow! {}",
        "Absolutely thrilled to share: {}"
    ]
}

def summarize_text(text, max_length=280):
    """Mock summarization for demo - uses smart truncation"""
    logger.info(f"[DEMO] Summarizing text to {max_length} characters")
    
    # If text is already short enough, return it as is
    if len(text) <= max_length:
        return text
    
    try:
        # Smart truncation with sentence boundaries
        sentences = text.split('. ')
        summary = ""
        for sentence in sentences:
            if len(summary) + len(sentence) + 2 <= max_length - 3:  # Allow space for period and ellipsis
                summary += sentence + ". "
            else:
                break
                
        if summary:
            return summary.strip()
        else:
            # If no complete sentence fits, just truncate with ellipsis
            return text[:max_length-3] + "..."
    except Exception as e:
        logger.error(f"Summarization error: {e}")
        # Final fallback: simple truncation with ellipsis
        return text[:max_length-3] + "..."

def generate_hashtags(text, num_tags=5):
    """Mock hashtag generation for demo - uses keyword matching"""
    logger.info(f"[DEMO] Generating {num_tags} hashtags")
    
    # Common business and social media hashtags categorized by topic
    hashtag_categories = {
        "business": ["Business", "Entrepreneur", "Startup", "Success", "Growth", "Innovation"],
        "marketing": ["Marketing", "SocialMedia", "Brand", "Audience", "Customer", "Engagement"],
        "technology": ["Tech", "Digital", "Software", "Online", "Platform", "AI"],
        "professional": ["Professional", "Leadership", "Career", "Networking", "Strategy", "Goals"],
        "content": ["Content", "ContentCreator", "CreativeContent", "Storytelling", "Quality"],
        "social": ["Community", "Connection", "Share", "Viral", "Trending", "Follow"]
    }
    
    default_tags = ["Business", "SocialMedia", "Success", "Growth", "Innovation"]
    
    try:
        selected_tags = []
        text_lower = text.lower()
        
        # Find matching keywords based on content
        keywords = {
            "business": ["company", "business", "entrepreneur", "startup", "revenue", "profit"],
            "marketing": ["brand", "audience", "customer", "market", "promotion", "campaign"],
            "technology": ["tech", "digital", "software", "online", "platform", "app", "ai", "tool"],
            "professional": ["team", "leadership", "career", "professional", "network", "strategy"],
            "content": ["content", "story", "creative", "design", "video", "photo", "post"],
            "social": ["social", "community", "share", "follow", "like", "viral", "trending"]
        }
        
        # Find matching categories
        matched_categories = []
        for category, words in keywords.items():
            for word in words:
                if word in text_lower and category not in matched_categories:
                    matched_categories.append(category)
                    break
        
        # Select hashtags from matched categories
        for category in matched_categories[:3]:  # Limit to 3 categories
            if category in hashtag_categories:
                available_tags = hashtag_categories[category]
                # Pick 1-2 random tags from each category
                category_tags = random.sample(available_tags, min(2, len(available_tags)))
                selected_tags.extend(category_tags)
        
        # If we don't have enough, add some generic ones
        while len(selected_tags) < num_tags:
            for tag in default_tags:
                if tag not in selected_tags and len(selected_tags) < num_tags:
                    selected_tags.append(tag)
        
        # Ensure we don't exceed the requested number
        selected_tags = selected_tags[:num_tags]
        
        return " ".join([f"#{tag}" for tag in selected_tags])
    except Exception as e:
        logger.error(f"Hashtag generation error: {e}")
        # Fallback to default hashtags
        return " ".join([f"#{tag}" for tag in default_tags[:num_tags]])

def adjust_tone_with_model(text, tone="professional"):
    """Mock tone adjustment for demo - uses template-based approach"""
    logger.info(f"[DEMO] Adjusting tone to: {tone}")
    
    # Use rule-based tone adjustment with enhanced templates
    return mock_tone_adjustment(text, tone)

def adjust_tone_with_openrouter(text, tone="professional"):
    """Mock OpenRouter function for demo - redirects to rule-based"""
    logger.info(f"[DEMO] Mock OpenRouter tone adjustment: {tone}")
    return mock_tone_adjustment(text, tone)

def mock_tone_adjustment(text, tone):
    """Enhanced rule-based tone adjustment with realistic variations"""
    try:
        # Get appropriate template based on tone and content analysis
        if "business" in text.lower() or "company" in text.lower() or "professional" in text.lower():
            content_type = "business"
        else:
            content_type = "general"
        
        template_key = f"{content_type}_{tone}"
        
        # If we have specific templates, use them
        if template_key in DEMO_TEMPLATES:
            templates = DEMO_TEMPLATES[template_key]
            template = random.choice(templates)
            
            # Apply the template while preserving the core message
            if "{}" in template:
                adjusted = template.format(text)
            else:
                adjusted = f"{template} {text}"
        else:
            # Fallback to basic tone adjustments
            adjusted = rule_based_tone_adjustment(text, tone)
        
        # Ensure reasonable length
        if len(adjusted) > 500:
            adjusted = adjusted[:497] + "..."
            
        return adjusted
        
    except Exception as e:
        logger.error(f"Mock tone adjustment error: {e}")
        return rule_based_tone_adjustment(text, tone)

def rule_based_tone_adjustment(text, tone):
    """Simple rule-based tone adjustment when AI services are unavailable"""
    if tone == "professional":
        # Remove casual language, exclamation marks, etc.
        adjusted = text.replace("!", ".")
        adjusted = adjusted.replace("hey", "hello")
        adjusted = adjusted.replace("yeah", "yes")
        adjusted = adjusted.replace("awesome", "excellent")
        # Add professional framing
        if len(adjusted) > 200:
            return f"We are pleased to share the following insights: {adjusted}"
        return adjusted
        
    elif tone == "casual":
        # Add more casual elements
        adjusted = text.replace(".", ".")  # Keep periods
        adjusted = adjusted.replace("Hello", "Hey")
        adjusted = adjusted.replace("Good day", "Hey there")
        # Add casual framing
        return f"Hey there! {adjusted}"
        
    elif tone == "enthusiastic":
        # Add enthusiasm
        sentences = text.split(". ")
        enthusiastic = []
        for i, sentence in enumerate(sentences):
            if i == len(sentences) - 1:
                enthusiastic.append(f"{sentence}!")
            else:
                enthusiastic.append(sentence)
        # Add enthusiastic framing
        return f"Exciting news! {'. '.join(enthusiastic)}"
    
    return text

def format_for_platform(text, platform):
    """Enhanced platform-specific formatting with realistic demo responses"""
    if not text or not platform:
        return text
        
    logger.info(f"[DEMO] Formatting content for platform: {platform}")
    
    try:
        # Remove markdown formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Remove bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)       # Remove italics
        
        if platform == "X":  # X (Twitter)
            # X has a 280 character limit
            if len(text) > 280:
                text = summarize_text(text, 280)
            
            # Add relevant hashtags (up to 2-3 for X)
            hashtags = generate_hashtags(text, 3)
            if hashtags:
                # Check if adding hashtags would exceed limit
                if len(text) + len(hashtags) + 1 <= 280:
                    text = f"{text} {hashtags}"
                else:
                    # Shorten text to make room for hashtags
                    available_space = 280 - len(hashtags) - 1
                    text = summarize_text(text, available_space)
                    text = f"{text} {hashtags}"
        
        elif platform == "IG":  # Instagram
            # Instagram loves visual storytelling
            emoji_sets = {
                "business": ["💼", "📊", "💡", "🚀", "✨"],
                "tech": ["💻", "🔧", "⚡", "🌐", "📱"],
                "creative": ["🎨", "✨", "🌟", "💫", "🔥"],
                "general": ["📸", "💯", "🌟", "✨", "🔥"]
            }
            
            # Determine content type for appropriate emojis
            content_type = "general"
            if any(word in text.lower() for word in ["business", "work", "professional", "company"]):
                content_type = "business"
            elif any(word in text.lower() for word in ["tech", "digital", "software", "app"]):
                content_type = "tech"
            elif any(word in text.lower() for word in ["creative", "design", "art", "photo"]):
                content_type = "creative"
            
            emojis = random.sample(emoji_sets[content_type], 3)
            hashtags = generate_hashtags(text, 8)  # Instagram allows more hashtags
            
            # Format with Instagram style
            formatted = f"{' '.join(emojis)}\n\n{text}\n\n{hashtags}\n\n{' '.join(emojis)}"
            return formatted
        
        elif platform == "LI":  # LinkedIn
            # Professional framing with industry insights
            linkedin_starters = [
                "💼 Professional insight:",
                "🎯 Industry perspective:",
                "📊 Market update:",
                "🚀 Business growth tip:",
                "💡 Thought leadership:",
                "📈 Strategic thinking:"
            ]
            
            starter = random.choice(linkedin_starters)
            
            # Add professional call-to-action
            cta_options = [
                "\n\nWhat are your thoughts on this? I'd love to hear from my professional network.",
                "\n\nHow has your experience been in this area? Share your insights below.",
                "\n\nWhat strategies have worked best for you? Let's discuss in the comments.",
                "\n\nI'm curious about your perspective on this trend. What do you think?"
            ]
            
            cta = random.choice(cta_options)
            
            if len(text) > 1000:
                text = summarize_text(text, 900)
            
            professional_hashtags = "#ThoughtLeadership #ProfessionalGrowth #BusinessInsights #Leadership"
            
            return f"{starter} {text}{cta}\n\n{professional_hashtags}"
        
        elif platform == "FB":  # Facebook
            # Conversational and community-focused
            fb_starters = [
                "Hey everyone! 👋",
                "Sharing some thoughts with my community:",
                "I wanted to share this with you all:",
                "Something interesting came up today:",
                "Quick update for my friends and followers:"
            ]
            
            starter = random.choice(fb_starters)
            
            # Add engagement question
            engagement_questions = [
                "\n\nWhat do you think about this?",
                "\n\nHave you experienced something similar?",
                "\n\nI'd love to hear your thoughts in the comments!",
                "\n\nWhat's your take on this? Let me know below!"
            ]
            
            question = random.choice(engagement_questions)
            
            return f"{starter}\n\n{text}{question}"
        
        elif platform == "TT":  # TikTok
            # Trendy and engaging with viral potential
            tiktok_hooks = [
                "POV: You discover this amazing thing ✨",
                "Tell me why this is so relatable 💯",
                "This just changed everything for me 🤯",
                "Nobody talks about this enough 📢",
                "Wait until you see this 👀"
            ]
            
            hook = random.choice(tiktok_hooks)
            trending_hashtags = generate_hashtags(text, 5)
            viral_tags = " #fyp #viral #trending #foryou"
            
            return f"{hook}\n\n{text}\n\n{trending_hashtags}{viral_tags}"
        
        elif platform == "YT":  # YouTube
            # Educational and comprehensive
            youtube_intros = [
                "🎥 In today's video, we're diving into:",
                "📺 Welcome back to the channel! Today's topic:",
                "🔴 New video alert! Let's explore:",
                "📹 Breaking down an important topic:"
            ]
            
            intro = random.choice(youtube_intros)
            
            # Add YouTube-style CTAs
            cta = "\n\n👍 If this was helpful, smash that like button!\n📺 Subscribe for more content like this\n� Let me know your thoughts in the comments below\n🔔 Ring the notification bell so you never miss an upload!"
            
            return f"{intro}\n\n{text}{cta}"
        
        return text  # Default format
    except Exception as e:
        logger.error(f"Error in platform formatting: {e}")
        return text  # Return original text on error

def adapt_content(text, platform, tone="professional"):
    """
    Adapt content for a specific platform and tone using AI models
    - First adjust tone
    - Then apply platform-specific formatting
    """
    logger.info(f"=== CONTENT ADAPTATION START ===")
    logger.info(f"Input text: '{text[:100]}{'...' if len(text) > 100 else ''}'")
    logger.info(f"Platform: {platform}, Tone: {tone}")
    
    try:
        # Validate inputs
        if not text or not text.strip():
            logger.error("No content provided")
            return "No content provided. Please enter your content to adapt."
        
        if not platform or platform not in ["X", "FB", "IG", "LI", "TT", "YT"]:
            logger.warning(f"Invalid platform: {platform}, using original text")
            return text
        
        # Step 1: Tone adjustment using AI
        logger.info(f"Step 1: Starting tone adjustment for tone '{tone}'")
        adjusted_text = text
        if tone and tone != "original":
            # Try using tone adjustment but fallback to original text if errors occur
            try:
                # Use our tone adjustment function that tries multiple methods
                logger.info("Attempting AI tone adjustment...")
                adjusted_text = adjust_tone_with_model(text, tone)
                
                # If we got back empty text, use rule-based adjustment
                if not adjusted_text or len(adjusted_text.strip()) < 10:
                    logger.warning("Empty or too short text from tone adjustment, using rule-based")
                    adjusted_text = rule_based_tone_adjustment(text, tone)
                    
                # Final validation - if something went wrong with rule-based too
                if not adjusted_text or len(adjusted_text.strip()) < 10:
                    logger.error("All tone adjustment methods failed, using original text")
                    adjusted_text = text
                else:
                    logger.info(f"Tone adjustment successful: '{adjusted_text[:100]}{'...' if len(adjusted_text) > 100 else ''}'")
            except Exception as e:
                logger.error(f"Tone adjustment error: {e}")
                # Use rule-based as fallback
                try:
                    adjusted_text = rule_based_tone_adjustment(text, tone)
                    logger.info("Used rule-based tone adjustment as fallback")
                except Exception as rule_error:
                    logger.error(f"Rule-based tone adjustment also failed: {rule_error}")
                    adjusted_text = text
        else:
            logger.info("No tone adjustment requested, using original text")
        
        # Step 2: Platform-specific formatting
        logger.info(f"Step 2: Starting platform formatting for '{platform}'")
        try:
            adapted_text = format_for_platform(adjusted_text, platform)
            
            # Final validation
            if not adapted_text or len(adapted_text.strip()) < 10:
                logger.error("Platform formatting returned invalid text, using adjusted text")
                adapted_text = adjusted_text
            else:
                logger.info(f"Platform formatting successful: '{adapted_text[:100]}{'...' if len(adapted_text) > 100 else ''}'")
        except Exception as format_error:
            logger.error(f"Platform formatting error: {format_error}")
            adapted_text = adjusted_text
        
        logger.info(f"=== CONTENT ADAPTATION COMPLETE ===")
        logger.info(f"Final result length: {len(adapted_text)} characters")
        return adapted_text
    except Exception as e:
        logger.error(f"Content adaptation error: {e}")
        # Absolute fallback: return original text with platform indicator
        platform_names = {
            "X": "X", 
            "FB": "Facebook", 
            "IG": "Instagram", 
            "LI": "LinkedIn", 
            "TT": "TikTok", 
            "YT": "YouTube"
        }
        
        platform_name = platform_names.get(platform, "Social Media")
        fallback_text = text
        
        # Add platform-specific fallback elements
        if platform == "X":  # X
            if len(fallback_text) > 280:
                fallback_text = fallback_text[:277] + "..."
        elif platform == "IG":  # Instagram
            if "#" not in fallback_text:
                fallback_text += "\n\n#content #social"
        elif platform == "LI":  # LinkedIn
            if len(fallback_text) < 100:
                fallback_text += "\n\nWhat are your thoughts on this? I'd love to hear from my professional network."
        
        logger.info(f"Using fallback formatting for {platform_name}")
        return fallback_text