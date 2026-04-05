import dataclasses
from typing import List, Optional
from datetime import datetime, timezone

from meeps.site.leaguepedia import leaguepedia
from meeps.parsers.query_builder import QueryBuilder


@dataclasses.dataclass
class Patch:
    """Represents a League of Legends patch from Leaguepedia.

    Attributes:
        patch: Patch version string (e.g., "14.1")
        release_date: Date the patch was released
        highlights: Summary of patch highlights
        patch_notes_link: URL to official patch notes
        disabled_champions: Comma-separated string of disabled champions
        disabled_items: Comma-separated string of disabled items
        new_champions: Comma-separated string of newly released champions
        updated_champions: Comma-separated string of updated champions
    """

    patch: Optional[str] = None
    release_date: Optional[datetime] = None
    highlights: Optional[str] = None
    patch_notes_link: Optional[str] = None
    disabled_champions: Optional[str] = None
    disabled_items: Optional[str] = None
    new_champions: Optional[str] = None
    updated_champions: Optional[str] = None

    @property
    def major_version(self) -> Optional[int]:
        """Returns the major version number (e.g., 14 for patch 14.1)."""
        if not self.patch:
            return None
        try:
            parts = self.patch.split(".")
            return int(parts[0]) if parts else None
        except (ValueError, IndexError):
            return None

    @property
    def minor_version(self) -> Optional[int]:
        """Returns the minor version number (e.g., 1 for patch 14.1)."""
        if not self.patch:
            return None
        try:
            parts = self.patch.split(".")
            return int(parts[1]) if len(parts) > 1 else None
        except (ValueError, IndexError):
            return None

    @property
    def disabled_champions_list(self) -> List[str]:
        """Returns disabled champions as a list."""
        if self.disabled_champions:
            return [c.strip() for c in self.disabled_champions.split(",") if c.strip()]
        return []

    @property
    def disabled_items_list(self) -> List[str]:
        """Returns disabled items as a list."""
        if self.disabled_items:
            return [i.strip() for i in self.disabled_items.split(",") if i.strip()]
        return []

    @property
    def new_champions_list(self) -> List[str]:
        """Returns new champions as a list."""
        if self.new_champions:
            return [c.strip() for c in self.new_champions.split(",") if c.strip()]
        return []

    @property
    def updated_champions_list(self) -> List[str]:
        """Returns updated champions as a list."""
        if self.updated_champions:
            return [c.strip() for c in self.updated_champions.split(",") if c.strip()]
        return []


# Fields to query for patch information
patches_fields = {
    "Patch",
    "ReleaseDate",
    "Highlights",
    "PatchNotesLink",
    "DisabledChampions",
    "DisabledItems",
    "NewChampions",
    "UpdatedChampions",
}


def _parse_patch_data(data: dict) -> Patch:
    """Parses raw API response data into a Patch object."""

    def parse_datetime(date_str: Optional[str]) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, AttributeError):
            return None

    return Patch(
        patch=data.get("Patch"),
        release_date=parse_datetime(data.get("ReleaseDate")),
        highlights=data.get("Highlights") or None,
        patch_notes_link=data.get("PatchNotesLink") or None,
        disabled_champions=data.get("DisabledChampions") or None,
        disabled_items=data.get("DisabledItems") or None,
        new_champions=data.get("NewChampions") or None,
        updated_champions=data.get("UpdatedChampions") or None,
    )


def get_patches(
    year: int = None,
    order_by: str = None,
    limit: int = None,
) -> List[Patch]:
    """Returns patch information from Leaguepedia.

    Args:
        year: Filter patches by year (based on release date)
        order_by: SQL ORDER BY clause (default: "Patches.ReleaseDate DESC")
        limit: Maximum number of patches to return

    Returns:
        A list of Patch objects

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    try:
        where_conditions = []

        if year:
            # Filter by year using YEAR function on ReleaseDate
            where_conditions.append(f"YEAR(Patches.ReleaseDate) = {int(year)}")

        where_clause = " AND ".join(where_conditions) if where_conditions else None

        query_kwargs = {}
        if limit:
            query_kwargs["limit"] = limit
        if order_by:
            query_kwargs["order_by"] = order_by
        else:
            query_kwargs["order_by"] = "Patches.ReleaseDate DESC"

        results = leaguepedia.query(
            tables="Patches",
            fields=",".join(patches_fields),
            where=where_clause,
            **query_kwargs,
        )

        return [_parse_patch_data(row) for row in results]

    except Exception as e:
        raise RuntimeError(f"Failed to fetch patches: {str(e)}")


def get_patch_by_version(patch_version: str) -> Optional[Patch]:
    """Returns a specific patch by version string.

    Args:
        patch_version: Patch version (e.g., "14.1")

    Returns:
        Patch object if found, None otherwise

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    try:
        where_clause = QueryBuilder.build_where("Patches", {"Patch": patch_version})

        results = leaguepedia.query(
            tables="Patches",
            fields=",".join(patches_fields),
            where=where_clause,
        )

        return _parse_patch_data(results[0]) if results else None

    except Exception as e:
        raise RuntimeError(f"Failed to fetch patch {patch_version}: {str(e)}")


def get_patches_in_date_range(
    start_date: datetime,
    end_date: datetime,
    order_by: str = None,
) -> List[Patch]:
    """Returns patches released within a date range.

    Args:
        start_date: Start of date range (inclusive)
        end_date: End of date range (inclusive)
        order_by: SQL ORDER BY clause (default: "Patches.ReleaseDate ASC")

    Returns:
        A list of Patch objects

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    try:
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        where_clause = (
            f"Patches.ReleaseDate >= '{start_str}' AND Patches.ReleaseDate <= '{end_str}'"
        )

        query_kwargs = {}
        if order_by:
            query_kwargs["order_by"] = order_by
        else:
            query_kwargs["order_by"] = "Patches.ReleaseDate ASC"

        results = leaguepedia.query(
            tables="Patches",
            fields=",".join(patches_fields),
            where=where_clause,
            **query_kwargs,
        )

        return [_parse_patch_data(row) for row in results]

    except Exception as e:
        raise RuntimeError(f"Failed to fetch patches in date range: {str(e)}")


def get_latest_patch() -> Optional[Patch]:
    """Returns the most recent patch.

    Returns:
        The most recent Patch object, or None if no patches found

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    try:
        results = leaguepedia.query(
            tables="Patches",
            fields=",".join(patches_fields),
            order_by="Patches.ReleaseDate DESC",
            limit=1,
        )

        return _parse_patch_data(results[0]) if results else None

    except Exception as e:
        raise RuntimeError(f"Failed to fetch latest patch: {str(e)}")


def get_patches_by_major_version(major_version: int, limit: int = None) -> List[Patch]:
    """Returns all patches for a specific major version (season).

    Args:
        major_version: Major version number (e.g., 14 for Season 14)
        limit: Maximum number of patches to return

    Returns:
        A list of Patch objects for the specified major version

    Raises:
        RuntimeError: If the Leaguepedia query fails
    """
    try:
        # Match patches starting with the major version followed by a dot
        escaped_version = QueryBuilder.escape(str(major_version))
        where_clause = f"Patches.Patch LIKE '{escaped_version}.%'"

        query_kwargs = {
            "order_by": "Patches.ReleaseDate ASC",
        }
        if limit:
            query_kwargs["limit"] = limit

        results = leaguepedia.query(
            tables="Patches",
            fields=",".join(patches_fields),
            where=where_clause,
            **query_kwargs,
        )

        return [_parse_patch_data(row) for row in results]

    except Exception as e:
        raise RuntimeError(f"Failed to fetch patches for version {major_version}: {str(e)}")
