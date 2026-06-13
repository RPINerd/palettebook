"""SQLAlchemy models for PaletteBook."""

from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Palette(Base):

    """
    A named collection of colors.

    Attributes:
        id: Primary key.
        name: Human-readable palette name.
        created_at: UTC timestamp of creation.
        updated_at: UTC timestamp of last modification.
        colors: Ordered list of Color rows belonging to this palette.
    """

    __tablename__ = "palettes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    colors: Mapped[list["Color"]] = relationship(
        "Color",
        back_populates="palette",
        cascade="all, delete-orphan",
        order_by="Color.position",
    )

    def to_dict(self, include_colors: bool = False) -> dict:
        """
        Serialise to a JSON-safe dictionary.

        Args:
            include_colors (bool): When True, embed the full color list.

        Returns:
            dict: Dictionary representation of the palette.
        """
        data = {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "color_count": len(self.colors),
        }
        if include_colors:
            data["colors"] = [c.to_dict() for c in self.colors]
        return data


class Color(Base):

    """
    A single color entry within a palette.

    Attributes:
        id: Primary key.
        palette_id: Foreign key to the parent palette.
        hex_value: Normalized 7-character hex string (e.g. #ff5733).
        name: Optional user-supplied label.
        position: Zero-based display order within the palette.
    """

    __tablename__ = "colors"

    id: Mapped[int] = mapped_column(primary_key=True)
    palette_id: Mapped[int] = mapped_column(ForeignKey("palettes.id"), nullable=False)
    hex_value: Mapped[str] = mapped_column(String(7), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    position: Mapped[int] = mapped_column(default=0)

    palette: Mapped["Palette"] = relationship("Palette", back_populates="colors")

    def to_dict(self) -> dict:
        """
        Serialise to a JSON-safe dictionary.

        Returns:
            dict: Dictionary representation of the color.
        """
        return {
            "id": self.id,
            "palette_id": self.palette_id,
            "hex_value": self.hex_value,
            "name": self.name,
            "position": self.position,
        }
