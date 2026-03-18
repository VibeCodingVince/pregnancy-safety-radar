"""
Base Agent class
Abstract interface for all agents
"""
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
import logging


class BaseAgent(ABC):
    """
    Base class for all agents
    Provides common infrastructure: database access, logging, execution interface
    """

    def __init__(self, db: Session):
        """
        Initialize agent with database session

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def execute(self, *args, **kwargs):
        """
        Execute the agent's primary function
        Must be implemented by subclasses

        Returns:
            Result depends on agent type
        """
        pass

    def log_info(self, message: str):
        """Log info message"""
        self.logger.info(message)

    def log_warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)

    def log_error(self, message: str):
        """Log error message"""
        self.logger.error(message)
