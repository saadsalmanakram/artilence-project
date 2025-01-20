from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import os
import json
import logging
from django.utils.timezone import now
from .models import Conversation

# Set up logging
logger = logging.getLogger(__name__)

# Ensure Hugging Face API key is set in environment variables
HUGGING_FACE_API_KEY = os.getenv("HUGGING_FACE_API_KEY")

# URL for Hugging Face API model
HF_API_URL = "https://api-inference.huggingface.co/models/distilbert/distilgpt2"

# Function to interact with the Hugging Face API
def get_ai_response(user_message):
    """
    Communicates with the Hugging Face API to generate a response based on the user's message.
    """
    headers = {"Authorization": f"Bearer {HUGGING_FACE_API_KEY}"}
    payload = {"inputs": user_message}

    try:
        response = requests.post(HF_API_URL, json=payload, headers=headers)

        if response.status_code == 200:
            return response.json()[0].get('generated_text', 'No response generated.')
        else:
            logger.error(f"Error from Hugging Face API: {response.text}")
            return "Sorry, I couldn't generate a response right now."

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        return "There was an error processing your request. Please try again later."

@csrf_exempt
def chat_api(request):
    """Handles full CRUD operations for chatbot conversations."""
    if request.method == 'POST':
        try:
            # Parse request body
            data = json.loads(request.body)
            user_message = data.get('user_message', '').strip()

            if not user_message:
                return JsonResponse({"error": "No user_message provided"}, status=400)

            # Get AI response
            ai_response = get_ai_response(user_message)

            # Store conversation in the database
            conversation = Conversation.objects.create(user_message=user_message, ai_response=ai_response)

            return JsonResponse({
                "id": conversation.id,
                "user_message": user_message,
                "ai_response": ai_response,
                "created_at": conversation.created_at.isoformat()
            })

        except json.JSONDecodeError:
            logger.error("Invalid JSON format in request body.")
            return JsonResponse({"error": "Invalid JSON format"}, status=400)

        except Exception as e:
            logger.error(f"Internal server error: {str(e)}")
            return JsonResponse({"error": f"Internal server error: {str(e)}"}, status=500)

    elif request.method == 'GET':
        """Retrieve past chatbot conversations."""
        conversations = Conversation.objects.all().values("id", "user_message", "ai_response", "created_at")
        return JsonResponse({"conversations": list(conversations)}, safe=False)

    elif request.method in ['PUT', 'PATCH']:
        """Update an existing chatbot conversation."""
        try:
            data = json.loads(request.body)
            conversation_id = data.get("id")
            new_user_message = data.get("user_message", "").strip()

            if not conversation_id:
                return JsonResponse({"error": "ID is required for updating"}, status=400)

            conversation = Conversation.objects.filter(id=conversation_id).first()
            if not conversation:
                return JsonResponse({"error": "Conversation not found"}, status=404)

            if new_user_message:
                conversation.user_message = new_user_message

                # Fetch new AI response based on updated message
                ai_response = get_ai_response(new_user_message)
                conversation.ai_response = ai_response

                conversation.save()

            return JsonResponse({
                "message": "Conversation updated",
                "id": conversation.id,
                "user_message": conversation.user_message,
                "ai_response": conversation.ai_response,
                "updated_at": now().isoformat()
            })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)

        except Exception as e:
            logger.error(f"Internal server error: {str(e)}")
            return JsonResponse({"error": f"Internal server error: {str(e)}"}, status=500)

    elif request.method == 'DELETE':
        """Delete a chatbot conversation."""
        try:
            data = json.loads(request.body)
            conversation_id = data.get("id")

            if not conversation_id:
                return JsonResponse({"error": "ID is required for deletion"}, status=400)

            conversation = Conversation.objects.filter(id=conversation_id).first()
            if not conversation:
                return JsonResponse({"error": "Conversation not found"}, status=404)

            conversation.delete()
            return JsonResponse({"message": "Conversation deleted successfully"})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)

        except Exception as e:
            logger.error(f"Internal server error: {str(e)}")
            return JsonResponse({"error": f"Internal server error: {str(e)}"}, status=500)

    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)
