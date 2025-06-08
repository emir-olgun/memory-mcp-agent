import ast  # Import ast to safely evaluate string representations of Python objects
from typing import List, Dict
import uuid
from schemas.chat_history import ChatMessage
from core.database import SessionLocal
from sqlalchemy.orm import Session
from datetime import datetime
from utils.email import send_email  # Assume you have a utility to send emails
import asyncio
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from models.chat_model import chat  # Chat model used for AI response streaming
from langchain.schema import HumanMessage  # Message schema for LangChain

Base = declarative_base()


# Define the Pluggr model to match your frontend schema
class Pluggr(Base):
    __tablename__ = "Pluggr"

    id = Column(String, primary_key=True)
    userId = Column(String, nullable=False)
    name = Column(String, nullable=False)
    domain = Column(String, nullable=False)
    avatar = Column(String, nullable=True)
    instructions = Column(String, nullable=True)
    reportsEmail = Column(String, nullable=True)
    botId = Column(String, unique=True, nullable=False)
    position = Column(String, default="bottom-right")
    theme = Column(String, default="light")
    createdAt = Column(DateTime, default=datetime.now)
    updatedAt = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    active = Column(Boolean, default=True)


def extract_chunk_texts(results) -> str:
    """
    Extracts all 'chunk_text' values from search results provided by Milvus.

    The function handles various result structures:
    - If results is a dict with a "data" key, it extracts the list from there.
    - If the result elements (or the entire results) are nested lists,
      it iterates through the inner lists.
    - It safely parses string representations if necessary.

    Returns:
    - A single string of all extracted 'chunk_text' values separated by newlines.
    """
    print("Extracting chunk texts from search results")
    
    chunk_texts = []  # List to hold the extracted texts
    document_ids = []  # List to hold the extracted document IDs
    # If results is a dictionary, extract its "data" key; otherwise assume it's a list.
    if isinstance(results, dict):
        results_data = results.get("data", [])
    else:
        results_data = results

    print(f"Processing {len(results_data)} result items")
    
    # Iterate over each element in the results. In your case, each element might itself be a list.
    for result in results_data:
        # If the result is a list, iterate through its items.
        if isinstance(result, list):
            for sub_result in result:
                # Process each sub_result as we would for a regular result.
                process_result_item(sub_result, chunk_texts, document_ids)
        else:
            # Process the result directly.
            process_result_item(result, chunk_texts, document_ids)

    print(f"Extracted {len(chunk_texts)} chunk texts from search results")
    return "\n".join(chunk_texts)


def process_result_item(result, chunk_texts_list, document_ids_list):
    """
    Helper function to process an individual result item.

    It handles:
    - String results: tries to parse them.
    - Dict results: extracts 'chunk_text' from the 'entity' key.
    - Custom objects with an 'entity' attribute.
    """
    # If the result is a string, parse it.
    if isinstance(result, str):
        try:
            result = ast.literal_eval(result)
            print("Parsed string result into Python object")
        except Exception as e:
            print(f"Error parsing result string: {str(e)}")
            return

    # If result is a dict, try to extract 'chunk_text' from 'entity'.
    if isinstance(result, dict):
        if "entity" in result:
            entity = result["entity"]
            if isinstance(entity, dict):
                chunk_text = entity.get("chunk_text")
                document_id = entity.get("document_id")
                if chunk_text:
                    chunk_texts_list.append(chunk_text)
                    document_ids_list.append(document_id)
                    print(f"Extracted chunk text from document ID: {document_id}")
                else:
                    print("'chunk_text' not found in entity dict")
            else:
                print(f"Unexpected type for 'entity': {type(entity)}")
        else:
            print("'entity' key not found in result dict")
    # If result isn't a dict but has an entity attribute, try that.
    elif hasattr(result, "entity"):
        entity = getattr(result, "entity")
        if isinstance(entity, dict):
            chunk_text = entity.get("chunk_text")
            document_id = entity.get("document_id")
            if chunk_text:
                chunk_texts_list.append(chunk_text)
                document_ids_list.append(document_id)
                print(f"Extracted chunk text from document ID: {document_id}")
            else:
                print("'chunk_text' field is missing in the entity attribute")
        else:
            print(f"'entity' attribute is not a dict but {type(entity)}")
    else:
        print(f"Unexpected result type in sub-item: {type(result)}")


def generate_augmented_prompt(
    user_query: str,
    pluggedIn_prompt: str,
    pluggr_prompt: str,
    relevant_info: str,
    wait_for_instruction: str = None,
    chat_history: str = None,
) -> str:
    """
    Augments the prepared prompt with chat history and relevant information from Milvus.

    Parameters:
    - prompt: The prepared prompt from the frontend.
    - relevant_info: Additional context gathered from Milvus search results.
    - chat_history: Optional chat history string.

    Returns:
    - A string containing the augmented prompt with context.
    """
    print(f"Generating augmented prompt for query: {user_query[:50]}...")
    
    # Handle case when chat_history is None or empty
    chat_history_section = (
        f"\nPrevious conversation:\n{chat_history}\n" if chat_history else ""
    )
    wait_for_instruction_section = (
        f"\nWait for instruction:\n{wait_for_instruction}\n"
        if wait_for_instruction
        else ""
    )
    user_query_section = (
        f"\nUser question, always respond to this question:\n{user_query}\n"
    )

    augmented_prompt = (
        f"{user_query_section}"
        f"{pluggedIn_prompt}\n"
        f"{pluggr_prompt}\n"
        f"{relevant_info}\n"
        f"{wait_for_instruction_section}\n"
        f"{chat_history_section}\n"
    )
    
    print(f"Augmented prompt generated with {len(relevant_info)} characters of relevant info")
    return augmented_prompt


conversation_cache = {}

async def get_chat_ids(pluggr_id: str) -> List[str]:
    """
    Retrieves all chat_ids for a given pluggr_id from the database.
    """
    db: Session = SessionLocal()
    try:
        # Query all chat_ids for the given pluggr_id
        chat_ids = (db.query(ChatMessage.chat_id)
                   .filter(ChatMessage.pluggr_id == pluggr_id)
                   .distinct()
                   .all())

        # Convert ORM objects to list of strings
        return [chat_id[0] for chat_id in chat_ids]
    except Exception as e:
        print(f"Error retrieving chat_ids: {str(e)}")
        raise
    finally:
        db.close()



async def get_chat_history(chat_id: str, pluggr_id: str) -> List[Dict]:
    """
    Retrieves complete chat history by combining database records with cached messages.
    Returns a list of dictionaries with message data.
    """
    print(f"Fetching chat history for chat_id: {chat_id}, pluggr_id: {pluggr_id}")
    
    # Get messages from database
    db: Session = SessionLocal()
    try:
        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.chat_id == chat_id, ChatMessage.pluggr_id == pluggr_id)
            .order_by(ChatMessage.timestamp.asc())
            .all()
        )

        print(f"Found {len(messages)} messages in database")

        # Convert ORM objects to dictionaries to avoid detached instance errors
        db_message_dicts = []
        for msg in messages:
            # Create a base message dictionary with fields that definitely exist
            message_dict = {
                "id": msg.id,
                "chat_id": msg.chat_id,
                "role": msg.role,
                "content": msg.content,
                "pluggr_id": msg.pluggr_id,
                "admin_id": getattr(msg, 'admin_id', None),
                "persona": getattr(msg, 'persona', None),
                "timestamp": msg.timestamp,
            }
            
            # Add admin_id and persona if they exist in the database schema
            # This is a safe way to handle the case where the columns don't exist yet
            try:
                if hasattr(msg, 'admin_id'):
                    message_dict["admin_id"] = msg.admin_id
                else:
                    message_dict["admin_id"] = None
                    
                if hasattr(msg, 'persona'):
                    message_dict["persona"] = msg.persona
                else:
                    message_dict["persona"] = None
            except Exception as e:
                print(f"Error accessing new fields: {str(e)}")
                message_dict["admin_id"] = None
                message_dict["persona"] = None
                
            db_message_dicts.append(message_dict)

        # Check if there are any cached messages that might not be in the database yet
        cached_messages = []
        if (
            chat_id in conversation_cache
            and isinstance(conversation_cache[chat_id], dict)
            and "messages" in conversation_cache[chat_id]
        ):
            cached_messages = conversation_cache[chat_id]["messages"]
            print(f"Found {len(cached_messages)} messages in cache")

            # Filter out cached messages that are already in the database
            db_message_ids = {msg["id"] for msg in db_message_dicts}
            new_cached_messages = [
                msg for msg in cached_messages if msg["id"] not in db_message_ids
            ]
            print(f"Found {len(new_cached_messages)} new messages in cache not yet in database")

            # Combine database messages with new cached messages
            combined_messages = db_message_dicts + new_cached_messages
        else:
            combined_messages = db_message_dicts

        # Update cache with the combined messages
        conversation_cache[chat_id] = {
            "messages": combined_messages,
            "last_message_time": datetime.now(),
        }

        print(f"Returning combined history with {len(combined_messages)} messages for chat_id: {chat_id}")
        return combined_messages
    except Exception as e:
        print(f"Error retrieving chat history: {str(e)}")
        raise
    finally:
        db.close()  # Ensure database connection is closed
        print("Database session closed")


async def save_message(chat_id: str, role: str, content: str, pluggr_id: str, admin_id: str = None, persona: str = None):
    """
    Save message to both cache and database
    
    Parameters:
        chat_id (str): The ID of the chat
        role (str): The role of the message sender ('user', 'assistant', or 'admin')
        content (str): The message content
        pluggr_id (str): The pluggr ID associated with the chat
        admin_id (str, optional): The ID of the admin (only used when role is 'admin')
        persona (str, optional): Optional persona identifier for future functionality
    """
    print(f"Saving {role} message for chat_id: {chat_id}, pluggr_id: {pluggr_id}")
    
    # Create new message with UUID as string to avoid type mismatch
    message_id = str(uuid.uuid4())  # Convert UUID to string

    # Create a dictionary representation for the cache
    message_dict = {
        "id": message_id,
        "chat_id": chat_id,
        "role": role,
        "content": content,
        "pluggr_id": pluggr_id,
        "admin_id": admin_id if role == "admin" else None,
        "persona": persona,
        "timestamp": datetime.now(),  # Add import for datetime if needed
    }

    # Ensure the chat_id is initialized as a dictionary in the cache
    if chat_id not in conversation_cache:
        conversation_cache[chat_id] = {
            "messages": [],
            "last_message_time": datetime.now(),
        }
    elif not isinstance(conversation_cache[chat_id], dict):
        # If it's not a dictionary, convert it to one
        conversation_cache[chat_id] = {
            "messages": conversation_cache[chat_id]
            if isinstance(conversation_cache[chat_id], list)
            else [],
            "last_message_time": datetime.now(),
        }
    elif "messages" not in conversation_cache[chat_id]:
        conversation_cache[chat_id]["messages"] = []

    conversation_cache[chat_id]["messages"].append(message_dict)
    conversation_cache[chat_id]["last_message_time"] = datetime.now()

    print(f"Added message to cache for chat_id {chat_id}. Cache now has {len(conversation_cache[chat_id]['messages'])} messages.")

    # Create the ORM object for database storage - only include fields that exist in the database
    try:
        message = ChatMessage(
            id=message_id, 
            chat_id=chat_id, 
            role=role, 
            content=content, 
            pluggr_id=pluggr_id
        )
        
        # Save to database
        db: Session = SessionLocal()
        try:
            db.add(message)
            db.commit()
            print(f"Saved message to database: id={message_id}, role={role}, chat_id={chat_id}")
        except Exception as e:
            print(f"Error saving message to database: {str(e)}")
            db.rollback()
        finally:
            db.close()
            print("Database session closed")
    except Exception as e:
        print(f"Error creating message object: {str(e)}")
        # Still keep the message in cache even if database save fails

    # After successfully saving the message, import and call the signal function
    try:
        from app.api.endpoints.chat import signal_chat_updated
        signal_chat_updated(chat_id)
    except ImportError:
        # Handle the case where the function can't be imported (to avoid circular imports)
        print("Could not import signal_chat_updated function")
    
    # Note: You might need to handle circular imports differently depending on your project structure


def serialize_chat_history(chat_history):
    """
    Convert chat history with datetime objects to a JSON-serializable format.
    """
    print(f"Serializing chat history with {len(chat_history)} messages")
    for message in chat_history:
        if "timestamp" in message and isinstance(message["timestamp"], datetime):
            message["timestamp"] = message["timestamp"].isoformat()
    return chat_history


def format_chat_history_for_email(chat_history):
    """
    Format chat history into a human-readable format for email.

    Args:
        chat_history: List of chat message dictionaries

    Returns:
        str: Formatted chat history as a string
    """
    print(f"Formatting chat history for email with {len(chat_history)} messages")
    
    # Convert all timestamps to strings first to avoid datetime comparison issues
    for message in chat_history:
        if "timestamp" in message and isinstance(message["timestamp"], datetime):
            message["timestamp_str"] = message["timestamp"].isoformat()

    # Sort messages by timestamp string to ensure correct order
    sorted_history = sorted(
        chat_history, key=lambda x: x.get("timestamp_str", x.get("timestamp", ""))
    )
    
    # Remove duplicate messages by tracking message content and role
    unique_messages = []
    seen_messages = set()  # Set to track unique (role, content) combinations
    
    for message in sorted_history:
        # Create a tuple of role and content to identify unique messages
        message_key = (message.get("role", ""), message.get("content", ""))
        
        # Only add the message if we haven't seen this combination before
        if message_key not in seen_messages:
            seen_messages.add(message_key)
            unique_messages.append(message)

    print(f"Removed {len(sorted_history) - len(unique_messages)} duplicate messages")

    # Format the chat history
    formatted_history = []
    formatted_history.append("=== CHAT HISTORY ===\n")

    current_date = None

    for message in unique_messages:
        # Extract timestamp
        timestamp = message.get("timestamp")

        # Format the timestamp
        if isinstance(timestamp, datetime):
            message_date = timestamp.strftime("%Y-%m-%d")
            timestamp_str = timestamp.strftime("%H:%M:%S")

            # Add date header if it's a new date
            if message_date != current_date:
                current_date = message_date
                formatted_history.append(f"\n[Date: {current_date}]\n")
        else:
            # Handle string timestamps
            try:
                if isinstance(timestamp, str):
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    message_date = dt.strftime("%Y-%m-%d")
                    timestamp_str = dt.strftime("%H:%M:%S")

                    # Add date header if it's a new date
                    if message_date != current_date:
                        current_date = message_date
                        formatted_history.append(f"\n[Date: {current_date}]\n")
                else:
                    timestamp_str = str(timestamp)
            except (ValueError, TypeError):
                timestamp_str = str(timestamp)
                print(f"Could not parse timestamp: {timestamp}")

        # Format the message
        role = message.get("role", "unknown").upper()
        content = message.get("content", "")

        formatted_history.append(f"[{timestamp_str}] {role}: {content}\n")

    print(f"Formatted chat history with {len(unique_messages)} messages")
    return "".join(formatted_history)


async def get_ai_summary(chat_history_text):
    """
    Send the formatted chat history to an AI model to get a summary.

    Args:
        chat_history_text: Formatted chat history as a string

    Returns:
        str: AI-generated summary of the conversation
    """
    print("Generating AI summary of chat history")
    try:
        # Create a prompt for the AI to summarize the conversation
        prompt = f"""Please summarize the following conversation in a concise paragraph:

{chat_history_text}

Summary:"""

        # Get the AI response
        complete_response = ""
        
        # Stream the AI response chunks using the existing chat model
        async for chunk in chat.astream(
            [HumanMessage(content=prompt)]
        ):
            # Append to the complete response
            complete_response += chunk.content

        # If the summary is too long, truncate it
        if len(complete_response) > 1000:
            print(f"Truncating summary from {len(complete_response)} to 1000 characters")
            complete_response = complete_response[:997] + "..."

        print(f"AI summary generated: {len(complete_response)} characters")
        return complete_response
    except Exception as e:
        print(f"Error generating AI summary: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return "Error generating summary. Please refer to the full conversation below."


async def check_inactive_chats():
    """
    Check for inactive chat sessions and send chat history via email if inactive for more than 5 minutes.
    """
    print("Starting background task to check for inactive chats")
    while True:
        current_time = datetime.now()
        for chat_id, data in list(conversation_cache.items()):
            last_message_time = data.get("last_message_time")
            if (
                last_message_time
                and (current_time - last_message_time).total_seconds() > 10
            ):  # Keeping the short timeout for testing
                print(f"Found inactive chat: {chat_id}, last activity: {last_message_time}")
                
                # Fetch complete chat history from the database
                db: Session = SessionLocal()
                try:
                    messages = (
                        db.query(ChatMessage)
                        .filter(ChatMessage.chat_id == chat_id)
                        .order_by(ChatMessage.timestamp.asc())
                        .all()
                    )

                    print(f"Retrieved {len(messages)} messages from database for chat_id: {chat_id}")

                    # Convert ORM objects to dictionaries
                    db_message_dicts = [
                        {
                            "id": msg.id,
                            "chat_id": msg.chat_id,
                            "role": msg.role,
                            "content": msg.content,
                            "pluggr_id": msg.pluggr_id,
                            "admin_id": getattr(msg, 'admin_id', None),
                            "persona": getattr(msg, 'persona', None),
                            "timestamp": msg.timestamp,  # Keep as datetime for now
                        }
                        for msg in messages
                    ]

                    # Get the pluggr_id from the first message
                    pluggr_id = None
                    if messages and hasattr(messages[0], "pluggr_id"):
                        pluggr_id = messages[0].pluggr_id
                        print(f"Found pluggr_id: {pluggr_id} for chat_id: {chat_id}")

                    # Initialize recipient_email to None - we'll only send if we find a valid email
                    recipient_email = None
                    if pluggr_id:
                        try:
                            from sqlalchemy import text

                            # Try to find by id
                            result = db.execute(
                                text(
                                    f"SELECT * FROM \"Pluggr\" WHERE id = '{pluggr_id}'"
                                )
                            ).fetchone()
                            if result:
                                result_dict = dict(result._mapping)
                                if (
                                    "reportsEmail" in result_dict
                                    and result_dict["reportsEmail"]
                                ):
                                    recipient_email = result_dict["reportsEmail"]
                                    print(f"Found recipient email: {recipient_email} for pluggr_id: {pluggr_id}")
                            else:
                                print(f"No direct match for pluggr_id: {pluggr_id}, trying partial matches")
                                # Check if pluggr_id is in any field
                                for field in ["id", "userId"]:
                                    query = f'SELECT * FROM "Pluggr" WHERE "{field}" LIKE \'%{pluggr_id}%\''
                                    result = db.execute(text(query)).fetchone()
                                    if result:
                                        result_dict = dict(result._mapping)
                                        if (
                                            "reportsEmail" in result_dict
                                            and result_dict["reportsEmail"]
                                        ):
                                            recipient_email = result_dict[
                                                "reportsEmail"
                                            ]
                                            print(f"Found recipient email via partial match: {recipient_email}")
                                        break

                        except Exception as e:
                            print(f"Error fetching pluggr information: {str(e)}")
                            import traceback
                            print(traceback.format_exc())

                    # Combine with any unsaved messages in the cache
                    cached_messages = data.get("messages", [])
                    complete_history = db_message_dicts + cached_messages
                    print(f"Combined history has {len(complete_history)} messages")

                    # Only send email if we found a valid recipient email
                    if recipient_email:
                        try:
                            # Format the chat history in a human-readable way
                            human_readable_history = format_chat_history_for_email(
                                complete_history
                            )

                            # Get AI summary of the conversation
                            print(f"Generating AI summary for chat_id {chat_id}")
                            ai_summary = await get_ai_summary(human_readable_history)
                            print(f"AI summary generated: {len(ai_summary)} characters")

                            # Create email content with summary and formatted history only (no JSON)
                            email_content = (
                                f"Chat History for Chat ID: {chat_id}\n\n"
                                f"AI Summary:\n{ai_summary}\n\n"
                                f"=== DETAILED CONVERSATION ===\n\n"
                                f"{human_readable_history}"
                            )

                            print(f"Sending chat history to email {recipient_email} for chat_id {chat_id}")

                            # Send email to the determined recipient
                            send_email(
                                recipient_email,
                                f"Chat Summary for {chat_id}",
                                email_content,
                            )
                            print(f"Email sent successfully to {recipient_email}")
                        except Exception as e:
                            print(f"Error sending email: {str(e)}")
                            import traceback
                            print(traceback.format_exc())
                    else:
                        print(f"No recipient email found for chat_id {chat_id}, skipping email")

                    # Remove the chat from cache after processing
                    del conversation_cache[chat_id]
                    print(f"Removed chat_id {chat_id} from cache")

                except Exception as e:
                    print(f"Error processing inactive chat {chat_id}: {str(e)}")
                    import traceback
                    print(traceback.format_exc())
                finally:
                    db.close()
                    print("Database session closed")

        print("Finished checking for inactive chats, sleeping for 60 seconds")
        await asyncio.sleep(5)  # Keeping the short check interval for testing
