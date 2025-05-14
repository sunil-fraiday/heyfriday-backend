import uuid
from datetime import timedelta
from mongoengine import Q

from app.models.mongodb.chat_session import ChatSession
from app.models.mongodb.chat_session_thread import ChatSessionThread
from app.models.mongodb.client import Client
from app.models.mongodb.utils import datetime_utc_now
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ThreadManager:
    """
    Service to manage session threads without modifying existing models.
    Provides functionality for creating threads, checking activity, and
    retrieving the appropriate thread for a given session ID.

    Threading will only be applied to sessions from clients with thread_config enabled.
    Otherwise, the default session behavior is maintained.
    """

    @staticmethod
    def format_thread_session_id(parent_id, thread_id):
        """Format the composite session_id"""
        return f"{parent_id}#{thread_id}"

    @staticmethod
    def parse_session_id(session_id):
        """Parse composite session_id into parent and thread components"""
        if session_id and "#" in session_id:
            parts = session_id.split("#", 1)
            return parts[0], parts[1]
        return session_id, None

    @classmethod
    def is_threading_enabled_for_client(cls, client):
        """Check if threading is enabled for a specific client object"""
        try:
            if not client:
                return False, None

            # Check if threading is enabled for this client
            if not client.thread_config or not isinstance(client.thread_config, dict):
                logger.info(f"Threading disabled for client {client.client_id}: No thread_config found")
                return False, None

            thread_config = client.thread_config
            if not thread_config.get("enabled", False):
                logger.info(f"Threading disabled for client {client.client_id}: thread_config.enabled=False")
                return False, None

            # Get inactivity minutes from config or use default (1440 min = 24 hours)
            inactivity_minutes = thread_config.get("inactivity_minutes", 1440)
            logger.info(
                f"Threading enabled for client {client.client_id} with inactivity_minutes={inactivity_minutes}"
            )

            return True, inactivity_minutes
        except Exception:
            # If we can't determine the config, disable threading
            return False, None

    @classmethod
    def is_threading_enabled_for_client_id(cls, client_id):
        """Check if threading is enabled for a client by ID"""
        try:
            if not client_id:
                return False, None

            # Get client by ID
            from app.services.client.client import ClientService

            client = ClientService.get_client(client_id)

            return cls.is_threading_enabled_for_client(client)
        except Exception:
            return False, None

    @classmethod
    def is_threading_enabled_for_session(cls, session_id):
        """Check if threading is enabled for the session's client"""
        try:
            # Find the session's client
            session = ChatSession.objects.get(Q(session_id=session_id) | Q(session_id__startswith=session_id))
            if not session.client:
                return False, None

            client = Client.objects.get(id=session.client.id)
            return cls.is_threading_enabled_for_client(client)
        except Exception:
            # If we can't determine the client or config, disable threading
            return False, None

    @classmethod
    def get_latest_thread(cls, parent_session_id):
        """Get the most recently active thread for a parent session"""
        return ChatSessionThread.objects.filter(parent_session_id=parent_session_id).order_by("-last_activity").first()

    @classmethod
    def is_thread_active(cls, thread, inactivity_minutes=1440):
        """
        Check if thread is active based on last activity timestamp.
        Thread is active if its last activity is within the inactivity_minutes threshold.
        """
        inactivity_threshold = datetime_utc_now() - timedelta(minutes=inactivity_minutes)
        return thread.last_activity >= inactivity_threshold

    @classmethod
    def get_chat_session(cls, parent_session_id):
        """Get the most recently active thread for a parent session"""
        return ChatSession.objects.filter(
            Q(session_id=parent_session_id) | Q(session_id__startswith=parent_session_id)
        ).first()

    @classmethod
    def deactivate_thread(cls, thread):
        """
        Deactivate a thread and its associated chat session
        
        Args:
            thread: The ChatSessionThread object to deactivate
        """
        if not thread or not thread.active:
            return False
            
        # Deactivate the thread
        thread.active = False
        thread.save()
        logger.info(f"Deactivated thread {thread.thread_id} for session {thread.parent_session_id}")
        
        # Also deactivate the associated chat session
        if thread.chat_session:
            logger.info(f"Deactivating chat session {thread.chat_session.session_id}")
            thread.chat_session.active = False
            thread.chat_session.save()
            
        return True
    
    @classmethod
    def close_active_threads(cls, parent_session_id):
        """Close (deactivate) all active threads for a parent session and their associated chat sessions"""
        # Find all active threads for this parent session
        existing_active_threads = ChatSessionThread.objects.filter(
            parent_session_id=parent_session_id, active=True
        )
        
        deactivated_count = 0
        # Deactivate all existing active threads
        for thread in existing_active_threads:
            if cls.deactivate_thread(thread):
                deactivated_count += 1
            
        return deactivated_count
    
    @classmethod
    def close_thread(cls, session_id, thread_id=None):
        """Close a specific thread or the latest active thread for a session"""
        parent_session_id = cls.parse_session_id(session_id)[0]
        
        if thread_id:
            # Close specific thread
            try:
                thread = ChatSessionThread.objects.get(parent_session_id=parent_session_id, thread_id=thread_id)
                if cls.deactivate_thread(thread):
                    logger.info(f"Closed thread {thread_id} for session {parent_session_id}")
                    return True
                else:
                    logger.info(f"Thread {thread_id} for session {parent_session_id} was already closed")
                    return False
            except Exception as e:
                logger.error(f"Failed to close thread {thread_id}: {str(e)}")
                return False
        else:
            # Close latest active thread
            latest_thread = cls.get_latest_thread(parent_session_id)
            if cls.deactivate_thread(latest_thread):
                logger.info(f"Closed latest thread {latest_thread.thread_id} for session {parent_session_id}")
                return True
            return False
    
    @classmethod
    def create_new_thread(cls, parent_session_id):
        """Create a new thread for an existing parent session"""
        try:
            # First try to find by session_id field
            parent_session = cls.get_chat_session(parent_session_id)
        except Exception:
            try:
                # Fallback to using the MongoDB id if session_id doesn't match
                parent_session = cls.get_chat_session(parent_session_id)
            except Exception as e:
                raise ValueError(f"Failed to find parent session: {str(e)}")

        # Deactivate any existing active threads for this parent session
        cls.close_active_threads(parent_session_id)

        # Generate new thread ID
        thread_id = str(uuid.uuid4())[:8]
        thread_session_id = cls.format_thread_session_id(parent_session_id, thread_id)

        # Create new ChatSession with threaded session_id
        new_session = ChatSession(
            session_id=thread_session_id,
            client=parent_session.client,
            client_channel=parent_session.client_channel,
            active=True,
            participants=parent_session.participants,
        )
        new_session.save()

        # Create thread tracking record
        thread = ChatSessionThread(
            parent_session_id=parent_session_id,
            thread_id=thread_id,
            thread_session_id=thread_session_id,
            chat_session=new_session,
            active=True,
            last_activity=datetime_utc_now(),
        )
        thread.save()
        
        logger.info(f"Created new thread: {thread_id} for session {parent_session_id}")

        return thread

    @classmethod
    def get_or_create_active_thread(
        cls, session_id, client=None, client_channel=None, force_new=False, inactivity_minutes=None
    ):
        """
        Core function to handle thread management logic for both new and existing sessions.

        This unified method can:
        1. Create a new session + thread when none exists yet (previously create_thread_with_session)
        2. Find or create a new thread for an existing session (previously get_or_create_active_thread)

        Parameters:
        - session_id: The session ID to find or create a thread for
        - client: Optional client object. If not provided, will try to find from existing sessions.
        - client_channel: Optional client channel object. If not provided, will try to find from existing sessions.
        - force_new: If True, always create a new thread regardless of existing active threads
        - inactivity_minutes: Threshold for thread inactivity in minutes (default uses client config or 1440 min = 24h)

        Returns:
        - The ChatSession to use (either an existing thread session or a new one)

        Raises:
        - ValueError: If no session exists and client wasn't provided, or if threading isn't enabled
        """
        # Parse session ID to get base ID (removing any thread part)
        base_session_id, _ = cls.parse_session_id(session_id)

        # First, check if any sessions exist with this base ID
        existing_sessions = list(ChatSession.objects.filter(session_id__startswith=f"{base_session_id}#"))
        session_exists = len(existing_sessions) > 0

        # If client wasn't provided, try to get it from existing sessions
        if client is None and session_exists:
            client = existing_sessions[0].client

        # If client_channel wasn't provided, try to get it from existing sessions
        if client_channel is None and session_exists:
            client_channel = existing_sessions[0].client_channel

        # If we have no sessions and no client was provided, we can't proceed
        if not session_exists and client is None:
            raise ValueError("Cannot create a thread without either an existing session or a client object")

        # Check if threading is enabled for this client
        threading_enabled, client_inactivity_minutes = cls.is_threading_enabled_for_client(client)

        # If threading is disabled, handle it directly
        if not threading_enabled:
            # No threading, check if session exists
            try:
                return ChatSession.objects.get(session_id=base_session_id)
            except Exception:
                # Create a new regular session
                if client:  # We have client info to create a new session
                    session = ChatSession(session_id=base_session_id, client=client, client_channel=client_channel)
                    session.save()
                    return session
                else:
                    raise ValueError("Cannot create session: threading is disabled and no session exists")

        # Threading is enabled - check if we need to use existing thread or create new one

        # Use client-specific inactivity minutes or provided default
        if inactivity_minutes is None:
            inactivity_minutes = client_inactivity_minutes if client_inactivity_minutes else 1440

        # Get latest thread for this parent session
        latest_thread = cls.get_latest_thread(base_session_id)

        # Check if we have a latest thread but it's inactive
        if latest_thread and not latest_thread.is_active(inactivity_minutes) and not force_new:
            logger.info(
                f"Found inactive thread {latest_thread.thread_id} for session {base_session_id} "
                f"(inactive for more than {inactivity_minutes} minutes)"
            )
            
        # Use existing thread if active and not forcing new
        if not force_new and latest_thread and latest_thread.is_active(inactivity_minutes):
            # Update activity timestamp
            latest_thread.update_activity()
            logger.info(f"Using existing active thread {latest_thread.thread_id} for session {base_session_id}")
            return latest_thread.chat_session

        # Check if this is a new session or we're creating a new thread for existing session
        if not session_exists:
            # Creating first thread for a new session
            # Generate a thread ID
            thread_id = str(uuid.uuid4())[:8]
            threaded_session_id = cls.format_thread_session_id(base_session_id, thread_id)

            logger.info(f"Creating first thread {thread_id} for new session {base_session_id}")

            # Create the session with thread ID
            session = ChatSession(session_id=threaded_session_id, client=client, client_channel=client_channel)
            session.save()

            # Create thread tracking record
            thread = ChatSessionThread(
                parent_session_id=base_session_id,
                thread_id=thread_id,
                thread_session_id=threaded_session_id,
                chat_session=session,
                active=True,
                last_activity=datetime_utc_now(),
            )
            thread.save()

            return session
        else:
            # Create a new thread for existing session
            logger.info(f"Creating new thread for existing session {base_session_id}")
            new_thread = cls.create_new_thread(base_session_id)
            return new_thread.chat_session

    @classmethod
    def list_threads(cls, parent_session_id, include_inactive=True):
        """List all threads for a parent session"""
        query = {"parent_session_id": parent_session_id}
        if not include_inactive:
            query["active"] = True

        return ChatSessionThread.objects.filter(**query).order_by("-last_activity")
