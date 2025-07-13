# ChapChap - AI-Powered Social Media Management

🚀 **Market-Ready Social Media Management Platform** - Automate your social media presence with AI-powered content adaptation and scheduling.

## ✨ Features

- **AI Content Adaptation**: Automatically adapt your content for different platforms (X, Facebook, Instagram, LinkedIn, TikTok, YouTube)
- **Smart Scheduling**: Schedule posts across multiple platforms with timezone support
- **Real-time Analytics**: Track engagement metrics and performance across all platforms
- **Enhanced X Integration**: Full X (Twitter) API v2 support with rate limiting and error handling
- **Beautiful UI**: Modern, responsive design with dark mode support
- **Draft Management**: Save drafts and edit them before publishing
- **Bulk Operations**: Manage multiple posts and platforms efficiently

## 🔧 Quick Setup

### Prerequisites
- Python 3.8+
- Django 4.2+
- X (Twitter) Developer Account
- PostgreSQL (recommended for production)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/chapchap.git
cd chapchap
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Run migrations**
```bash
python manage.py migrate
```

6. **Create superuser**
```bash
python manage.py createsuperuser
```

7. **Start the server**
```bash
python manage.py runserver
```

## 🔑 X (Twitter) API Setup

### Step 1: Get X Developer Account
1. Go to [developer.twitter.com](https://developer.twitter.com/)
2. Apply for a developer account
3. Create a new app in the developer portal

### Step 2: Get API Credentials
You need these 5 credentials from your X app:

1. **API Key** (Consumer Key)
2. **API Secret** (Consumer Secret)
3. **Access Token**
4. **Access Token Secret**
5. **Bearer Token**

### Step 3: Configure Environment Variables
Add these to your `.env` file:

```env
# X (Twitter) API Credentials
X_API_KEY=your_api_key_here
X_API_SECRET=your_api_secret_here
X_ACCESS_TOKEN=your_access_token_here
X_ACCESS_TOKEN_SECRET=your_access_token_secret_here
X_BEARER_TOKEN=your_bearer_token_here
```

### Step 4: Validate Setup
1. Go to Settings in ChapChap
2. Click "Validate Credentials" to test your X API setup
3. Click "Test Post" to send a test tweet

## 🎯 Recommended AI Models

For enhanced content adaptation, add these optional AI services:

### Free Options:
- **Hugging Face Transformers** (Free tier: 1,000 requests/month)
  ```env
  HUGGINGFACE_API_KEY=your_huggingface_token
  ```

### Paid Options:
- **OpenAI GPT-4** (Best quality, ~$0.03/1k tokens)
  ```env
  OPENAI_API_KEY=your_openai_key
  ```

- **OpenRouter** (Access to multiple models, competitive pricing)
  ```env
  OPENROUTER_API_KEY=your_openrouter_key
  ```

## 📊 Platform Support

| Platform | Status | Features |
|----------|--------|----------|
| X (Twitter) | ✅ Full Support | Posts, Media, Analytics, Rate Limiting |
| Facebook | 🔄 Basic Support | Text Posts, Basic Analytics |
| Instagram | 🔄 Basic Support | Photo Posts, Captions |
| LinkedIn | 🔄 Basic Support | Professional Posts |
| TikTok | 📝 Planned | Video Posts (API approval required) |
| YouTube | 📝 Planned | Video Upload & Management |

## 🚀 Production Deployment

### Using Render (Recommended)

1. **Push to GitHub**
```bash
git add .
git commit -m "Ready for production"
git push origin main
```

2. **Deploy to Render**
- Connect your GitHub repository
- Set environment variables
- Deploy automatically

### Environment Variables for Production
```env
DEBUG=False
SECRET_KEY=your_production_secret_key
DATABASE_URL=your_database_url
X_API_KEY=your_x_api_key
X_API_SECRET=your_x_api_secret
X_ACCESS_TOKEN=your_x_access_token
X_ACCESS_TOKEN_SECRET=your_x_access_token_secret
X_BEARER_TOKEN=your_x_bearer_token
```

## 📈 Analytics & Monitoring

ChapChap provides comprehensive analytics:

- **Engagement Metrics**: Likes, shares, comments, impressions
- **Performance Tracking**: Post performance over time
- **Platform Comparison**: Compare performance across platforms
- **Audience Insights**: Understand your audience engagement patterns

## 🔒 Security Features

- **Rate Limiting**: Automatic rate limiting for all APIs
- **Token Encryption**: Secure storage of API credentials
- **Audit Logging**: Track all publishing activities
- **Error Handling**: Comprehensive error handling and recovery

## 🎨 Customization

### Themes
- Light/Dark mode toggle
- Responsive design for all devices
- Modern UI with Tailwind CSS

### Content Adaptation
- Professional tone for business content
- Casual tone for personal brands
- Enthusiastic tone for marketing campaigns

## 🆘 Troubleshooting

### Common Issues

1. **X API Credentials Invalid**
   - Verify all 5 credentials are correct
   - Check if your X app has the right permissions
   - Ensure Bearer Token is generated

2. **Rate Limit Exceeded**
   - ChapChap automatically handles rate limiting
   - Posts are queued and published when limits reset

3. **Content Adaptation Fails**
   - Check if AI service credentials are configured
   - Fallback to rule-based adaptation if AI fails

### Getting Help

- Check the [Issues](https://github.com/yourusername/chapchap/issues) page
- Join our [Discord](https://discord.gg/chapchap) community
- Email support: support@chapchap.com

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with Django and modern web technologies
- AI-powered content adaptation
- Inspired by the need for efficient social media management

---

**Ready to automate your social media presence?** 🚀

[Get Started](https://chapchap.com) | [Documentation](https://docs.chapchap.com) | [Support](https://support.chapchap.com)
