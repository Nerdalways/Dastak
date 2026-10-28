import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Float,
    Enum,
    ForeignKey,
    Text,
    Integer,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class VendorType(str, enum.Enum):
    ROAMING = "ROAMING"  # Moving pushcarts (thelas)
    STATIC = "STATIC"    # Fixed corner kiosks / repair stalls


class VendorStatus(str, enum.Enum):
    VERIFIED_OPEN = "VERIFIED_OPEN"  # Active via physical anchor / heartbeat
    LIKELY_OPEN = "LIKELY_OPEN"      # Within operating hours window
    CLOSED = "CLOSED"


class PresetBundle(str, enum.Enum):
    STAPLES = "STAPLES"              # Aloo, Pyaz, Tamatar, Mirchi, Dhaniya
    GREENS = "GREENS"                # Palak, Methi, Bhindi, Gobi
    FRUITS = "FRUITS"                # Seasonal Fruits
    CUSTOM = "CUSTOM"


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(String(32), primary_key=True)  # e.g., "V-DEL-1049"
    name = Column(String(128), nullable=False)
    phone_hash = Column(String(64), nullable=False, unique=True, index=True)
    vendor_type = Column(Enum(VendorType), nullable=False, default=VendorType.ROAMING)
    status = Column(Enum(VendorStatus), nullable=False, default=VendorStatus.CLOSED)
    
    # 3-Preset Inventory Model
    active_bundle = Column(Enum(PresetBundle), default=PresetBundle.STAPLES)
    canopy_number = Column(Integer, nullable=True)  # High-contrast 3-digit visual ID (#104)

    # Trust & Identity Verification (RWA Clearance)
    is_verified = Column(Boolean, default=False)
    verification_source = Column(String(64), nullable=True)  # "e-Shram", "PM-SVANidhi", "RWA-Pass"

    # Spatial Tracking & Heartbeat
    current_h3_res9 = Column(String(15), nullable=True, index=True)
    last_lat = Column(Float, nullable=True)
    last_lon = Column(Float, nullable=True)
    last_heartbeat = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Physical Milestone Anchor link (for static vendors)
    anchor_id = Column(String(32), ForeignKey("milestone_anchors.id"), nullable=True)
    anchor = relationship("MilestoneAnchor", back_populates="static_vendors")


class MilestoneAnchor(Base):
    __tablename__ = "milestone_anchors"

    id = Column(String(32), primary_key=True)  # e.g., "M-ROH-SEC9-PEEPAL"
    name = Column(String(128), nullable=False)  # "Peepal Chowk / Sharma Chai"
    h3_res9 = Column(String(15), nullable=False, index=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)

    static_vendors = relationship("Vendor", back_populates="anchor")


class ZoneSubscription(Base):
    """Anonymous resident WebPush subscriptions with dual-tier spatial scoping."""
    __tablename__ = "zone_subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Tier 1 & Tier 2 Spatial Scoping
    h3_res9 = Column(String(15), nullable=False, index=True)           # L1 Hexagon (~100m)
    street_segment_id = Column(String(64), nullable=True, index=True) # Sub-cell Gali filter
    zone_label = Column(String(64), nullable=True)                    # "ROHINI_SEC9_TOWERC"

    # RFC 8291 WebPush Device Target (Zero-PII)
    endpoint = Column(Text, nullable=False, unique=True)
    p256dh = Column(String(128), nullable=False)
    auth = Column(String(64), nullable=False)

    # Health & Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_notified = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        Index("idx_h3_street", "h3_res9", "street_segment_id"),
    )