"""Shared folders — two users can share a folder, both read/add, only adder deletes own items."""
from typing import List, Dict, Optional

from desktop_app.utils.logger import get_logger

logger = get_logger()


class SharedService:
    def __init__(self, supabase=None):
        self.supabase = supabase

    def _ok(self) -> bool:
        return bool(self.supabase and self.supabase.available)

    def create_folder(self, owner: str, partner: str,
                      name: str = "Shared") -> Optional[Dict]:
        if not self._ok():
            return None
        try:
            result = self.supabase._client.table("shared_folders").insert({
                "name": name, "owner_username": owner,
                "partner_username": partner,
            }).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"create_folder: {e}")
            return None

    def get_folders_for_user(self, username: str) -> List[Dict]:
        if not self._ok():
            return []
        try:
            r1 = (self.supabase._client.table("shared_folders")
                  .select("*").eq("owner_username", username).execute())
            r2 = (self.supabase._client.table("shared_folders")
                  .select("*").eq("partner_username", username).execute())
            folders = (r1.data or []) + (r2.data or [])
            seen = set()
            unique = []
            for f in folders:
                if f["id"] not in seen:
                    seen.add(f["id"])
                    unique.append(f)
            return unique
        except Exception as e:
            logger.error(f"get_folders: {e}")
            return []

    def get_items(self, folder_id: str) -> List[Dict]:
        if not self._ok():
            return []
        try:
            result = (self.supabase._client.table("shared_items")
                      .select("*").eq("folder_id", folder_id)
                      .order("created_at", desc=True).execute())
            return result.data or []
        except Exception as e:
            logger.error(f"get_items: {e}")
            return []

    def add_item(self, folder_id: str, added_by: str,
                 content: str, content_type: str = "text") -> Optional[Dict]:
        if not self._ok():
            return None
        try:
            result = self.supabase._client.table("shared_items").insert({
                "folder_id": folder_id, "added_by": added_by,
                "content": content, "content_type": content_type,
            }).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"add_item: {e}")
            return None

    def delete_item(self, item_id: str, username: str,
                    is_admin: bool = False) -> bool:
        """Only the adder or admin can delete."""
        if not self._ok():
            return False
        try:
            if is_admin:
                self.supabase._client.table("shared_items").delete().eq("id", item_id).execute()
                return True
            self.supabase._client.table("shared_items").delete().eq("id", item_id).eq("added_by", username).execute()
            return True
        except Exception as e:
            logger.error(f"delete_item: {e}")
            return False

    def delete_folder(self, folder_id: str, username: str,
                      is_admin: bool = False) -> bool:
        if not self._ok():
            return False
        try:
            if is_admin:
                self.supabase._client.table("shared_folders").delete().eq("id", folder_id).execute()
                return True
            self.supabase._client.table("shared_folders").delete().eq("id", folder_id).eq("owner_username", username).execute()
            return True
        except Exception as e:
            logger.error(f"delete_folder: {e}")
            return False
