import uuid
from datetime import timedelta
from mongoengine import Q

from app.models.mongodb.chat_session import ChatSession
from app.models.mongodb.chat_session_thread import ChatSessionThread
from app.models.mongodb.client import Client
from app.models.mongodb.utils import datetime_utc_now


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
                return False, None

            thread_config = client.thread_config
            if not thread_config.get("enabled", False):
                return False, None

            # Get inactivity minutes from config or use default (1440 min = 24 hours)
            inactivity_minutes = thread_config.get("inactivity_minutes", 1440)

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
        return ChatSession.objects.filter(Q(session_id=parent_session_id) | Q(session_id__startswith=parent_session_id)).first()

    @classmethod
    def create_new_thread(cls, parent_session_id):
        """Create a new thread for the given parent session"""
        try:
            # First try to find by session_id field
            parent_session = cls.get_chat_session(parent_session_id)
        except Exception:
            try:
                # Fallback to using the MongoDB id if session_id doesn't match
                parent_session = cls.get_chat_session(parent_session_id)
            except Exception as e:
                raise ValueError(f"Failed to find parent session: {str(e)}")

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

        # Check if we should use existing thread
        if not force_new and latest_thread and latest_thread.is_active(inactivity_minutes):
            # Update activity timestamp
            latest_thread.update_activity()
            return latest_thread.chat_session

        # Check if this is a new session or we're creating a new thread for existing session
        if not session_exists:
            # Creating first thread for a new session
            # Generate a thread ID
            thread_id = str(uuid.uuid4())[:8]
            threaded_session_id = cls.format_thread_session_id(base_session_id, thread_id)

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
            new_thread = cls.create_new_thread(base_session_id)
            return new_thread.chat_session

    @classmethod
    def list_threads(cls, parent_session_id, include_inactive=True):
        """List all threads for a parent session"""
        query = {"parent_session_id": parent_session_id}
        if not include_inactive:
            query["active"] = True

        return ChatSessionThread.objects.filter(**query).order_by("-last_activity")
