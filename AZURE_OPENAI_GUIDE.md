# Azure OpenAI Integration Guide

This guide explains how to use Azure OpenAI API Key with your LangGraph project.

## Prerequisites

1. **Azure OpenAI Resource**: You need an Azure OpenAI resource deployed in Azure
2. **API Key**: Get your API key from the Azure portal
3. **Deployment**: Create a model deployment (e.g., GPT-4, GPT-3.5-turbo)

## Setup Steps

### 1. Install Required Packages

First, activate your virtual environment and install the Azure OpenAI package:

```powershell
.\lg-demo\Scripts\Activate.ps1
pip install langchain-openai azure-identity
```

### 2. Configure Environment Variables

Update your `.env` file with your Azure OpenAI credentials:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_actual_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
```

**To find these values:**
- **API Key**: Azure Portal → Your OpenAI Resource → Keys and Endpoint
- **Endpoint**: Azure Portal → Your OpenAI Resource → Keys and Endpoint  
- **Deployment Name**: Azure Portal → Your OpenAI Resource → Model deployments

### 3. Update Your Code

Here's how to modify your existing code to use Azure OpenAI:

```python
import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

load_dotenv()

# Initialize Azure OpenAI
llm = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    temperature=0.7,
    max_tokens=1000,
)
```

## Authentication Methods

### Method 1: API Key (Current)
- Simple to set up
- Good for development and testing
- Requires manual key rotation

### Method 2: Azure Active Directory (Recommended for Production)
```python
from azure.identity import DefaultAzureCredential
from langchain_openai import AzureChatOpenAI

credential = DefaultAzureCredential()

llm = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_ad_token_provider=credential.get_token,
)
```

## Best Practices

### Security
- ✅ Store credentials in environment variables or Azure Key Vault
- ✅ Use Azure AD authentication in production
- ❌ Never hardcode API keys in your source code
- ✅ Implement credential rotation

### Error Handling
```python
def chatbot_with_retry(state: State):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = llm.invoke(state["messages"])
            return {"messages": [response]}
        except Exception as e:
            if attempt == max_retries - 1:
                # Final attempt failed
                return {"messages": [{"role": "assistant", "content": "Service temporarily unavailable"}]}
            time.sleep(2 ** attempt)  # Exponential backoff
```

### Performance
- Use connection pooling for high-volume applications
- Implement caching for repeated queries
- Monitor token usage and costs
- Set appropriate timeout values

## Testing Your Setup

1. Run the example code:
```powershell
python main_azure.py
```

2. If you see "Using Azure OpenAI..." - you're connected!
3. If you see "Azure OpenAI not configured..." - check your environment variables

## Troubleshooting

### Common Issues

**"Import langchain_openai could not be resolved"**
```powershell
pip install langchain-openai
```

**"Authentication failed"**
- Verify your API key is correct
- Check that your endpoint URL is correct
- Ensure your deployment name matches exactly

**"Model not found"**
- Verify your deployment name in Azure portal
- Ensure the model is deployed and running

**"Rate limit exceeded"**
- Implement retry logic with exponential backoff
- Monitor your usage in Azure portal
- Consider upgrading your pricing tier

## Cost Management

- Monitor usage in Azure portal
- Set up billing alerts
- Use cheaper models for development (GPT-3.5 vs GPT-4)
- Implement token counting to track costs

## Next Steps

1. Update your main.py to use Azure OpenAI
2. Test with different models (GPT-4, GPT-3.5-turbo)
3. Implement proper error handling
4. Set up monitoring and logging
5. Consider moving to Azure AD authentication for production

## Resources

- [Azure OpenAI Documentation](https://docs.microsoft.com/en-us/azure/cognitive-services/openai/)
- [LangChain Azure OpenAI Integration](https://python.langchain.com/docs/integrations/chat/azure_chat_openai)
- [Azure Identity Documentation](https://docs.microsoft.com/en-us/python/api/azure-identity/)