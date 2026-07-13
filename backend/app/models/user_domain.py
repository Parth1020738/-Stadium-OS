from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from backend.app.models.auth import Base, user_roles

class UserStatus(str, enum.Enum):
    PENDING = "Pending"
    ACTIVE = "Active"
    DEACTIVATED = "Deactivated"

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    details = Column(String, nullable=True)

    departments = relationship("Department", back_populates="organization", cascade="all, delete-orphan")

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)

    organization = relationship("Organization", back_populates="departments")
    teams = relationship("Team", back_populates="department", cascade="all, delete-orphan")

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=False)

    department = relationship("Department", back_populates="teams")
    profiles = relationship("UserProfile", back_populates="team")

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)

    user = relationship("User", back_populates="profile")
    team = relationship("Team", back_populates="profiles")

class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    language = Column(String, default="en")
    receive_notifications = Column(Boolean, default=True)

    user = relationship("User", back_populates="preferences")
