import os

from django.core.exceptions import ImproperlyConfigured
from mssql.base import DatabaseWrapper as MssqlDatabaseWrapper


class DatabaseWrapper(MssqlDatabaseWrapper):
    def get_new_connection(self, conn_params):
        domain = conn_params.get("DOMAIN", "")
        if not domain:
            return super().get_new_connection(conn_params)
        if os.name != "nt":
            raise ImproperlyConfigured(
                "DJANGO_DB_DOMAIN credentials require a Windows backend host."
            )
        if not conn_params.get("USER") or not conn_params.get("PASSWORD"):
            raise ImproperlyConfigured(
                "DJANGO_DB_DOMAIN requires DJANGO_DB_USER and DJANGO_DB_PASSWORD."
            )

        import pywintypes
        import win32api
        import win32con
        import win32security

        previous_token = None
        try:
            previous_token = win32security.OpenThreadToken(
                win32api.GetCurrentThread(),
                win32con.TOKEN_QUERY | win32con.TOKEN_IMPERSONATE,
                True,
            )
        except pywintypes.error as exc:
            if exc.winerror != 1008:
                raise

        token = None
        impersonating = False
        try:
            token = win32security.LogonUser(
                conn_params["USER"],
                domain,
                conn_params["PASSWORD"],
                win32con.LOGON32_LOGON_NEW_CREDENTIALS,
                win32con.LOGON32_PROVIDER_WINNT50,
            )
            win32security.ImpersonateLoggedOnUser(token)
            impersonating = True
            trusted_params = dict(conn_params, USER="", PASSWORD="")
            return super().get_new_connection(trusted_params)
        finally:
            try:
                if impersonating:
                    if previous_token is not None:
                        win32security.SetThreadToken(None, previous_token)
                    else:
                        win32security.RevertToSelf()
            finally:
                if token is not None:
                    token.Close()
                if previous_token is not None:
                    previous_token.Close()