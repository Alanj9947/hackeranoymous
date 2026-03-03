"""Twilio service for phone number provisioning and call handling."""

from __future__ import annotations

import logging
from typing import Optional, Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


class NumberCapability(str, Enum):
    """Phone number capability types."""
    VOICE = "voice"
    SMS = "sms"
    MMS = "mms"
    FAX = "fax"


class TwilioService:
    """Manage Twilio phone numbers and inbound calls."""

    def __init__(self, account_sid: str, auth_token: str):
        """
        Initialize Twilio service.

        Args:
            account_sid: Twilio Account SID
            auth_token: Twilio Auth Token
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        
        try:
            from twilio.rest import Client
            self.client = Client(account_sid, auth_token)
            logger.info("Twilio client initialized")
        except ImportError:
            logger.error("twilio-python not installed")
            raise ImportError("Install twilio-python: pip install twilio")
        except Exception as e:
            logger.error(f"Error initializing Twilio client: {str(e)}")
            raise

    async def get_available_numbers(
        self,
        country: str = "US",
        area_code: Optional[str] = None,
        sms_enabled: bool = True,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Search for available phone numbers.

        Args:
            country: Country code (US, CA, GB, AU, etc.)
            area_code: Area code to filter (US only)
            sms_enabled: Include SMS capability
            limit: Maximum results to return

        Returns:
            List of available numbers with details
        """
        try:
            logger.info(f"Searching available numbers: country={country}, area_code={area_code}")

            if country == "US":
                # US numbers with area code
                numbers_list = self.client.available_phone_numbers(country).local.stream(
                    area_code=area_code,
                    sms_enabled=sms_enabled,
                    limit=limit,
                )
            elif country == "CA":
                # Canadian numbers
                numbers_list = self.client.available_phone_numbers(country).local.stream(
                    area_code=area_code,
                    sms_enabled=sms_enabled,
                    limit=limit,
                )
            else:
                # International numbers (no area code)
                numbers_list = self.client.available_phone_numbers(country).local.stream(
                    sms_enabled=sms_enabled,
                    limit=limit,
                )

            results = []
            for number_obj in numbers_list:
                results.append({
                    "phone_number": number_obj.phone_number,
                    "friendly_name": number_obj.friendly_name,
                    "locality": getattr(number_obj, "locality", ""),
                    "region": getattr(number_obj, "region", ""),
                    "postal_code": getattr(number_obj, "postal_code", ""),
                    "country_code": country,
                    "sms_capable": True,
                    "voice_capable": True,
                })

            logger.info(f"Found {len(results)} available numbers")
            return results

        except Exception as e:
            logger.error(f"Error searching available numbers: {str(e)}")
            raise Exception(f"Failed to search numbers: {str(e)}") from e

    async def provision_phone_number(
        self,
        phone_number: str,
        company_id: str,
        agent_id: str,
        webhook_url: str,
    ) -> Dict[str, Any]:
        """
        Provision (purchase) a phone number.

        Args:
            phone_number: Phone number to purchase
            company_id: Company ID
            agent_id: Agent ID
            webhook_url: Webhook URL for incoming calls

        Returns:
            Provisioning result with Twilio SID and details
        """
        try:
            logger.info(f"Provisioning number: {phone_number} for agent {agent_id}")

            # Purchase the number
            incoming_phone_number = self.client.incoming_phone_numbers.create(
                phone_number=phone_number,
                friendly_name=f"Agent {agent_id[:8]}",
                sms_method="POST",
                sms_url=webhook_url,
                voice_method="POST",
                voice_url=webhook_url,
                voice_fallback_method="POST",
                voice_fallback_url=webhook_url,
                status_callback_method="POST",
                status_callback_url=webhook_url,
            )

            result = {
                "twilio_phone_sid": incoming_phone_number.sid,
                "phone_number": incoming_phone_number.phone_number,
                "friendly_name": incoming_phone_number.friendly_name,
                "status": "active",
                "provisioned_at": str(incoming_phone_number.date_created),
                "monthly_cost": 1.00,  # Typical Twilio cost
                "webhook_url": webhook_url,
                "webhook_configured_at": str(incoming_phone_number.date_created),
            }

            logger.info(f"Number provisioned successfully: {result['twilio_phone_sid']}")
            return result

        except Exception as e:
            logger.error(f"Error provisioning number: {str(e)}")
            raise Exception(f"Failed to provision number: {str(e)}") from e

    async def release_phone_number(self, twilio_phone_sid: str) -> bool:
        """
        Release (delete) a phone number.

        Args:
            twilio_phone_sid: Twilio phone number SID

        Returns:
            True if successful
        """
        try:
            logger.info(f"Releasing number: {twilio_phone_sid}")

            self.client.incoming_phone_numbers(twilio_phone_sid).delete()
            logger.info(f"Number released: {twilio_phone_sid}")
            return True

        except Exception as e:
            logger.error(f"Error releasing number: {str(e)}")
            raise Exception(f"Failed to release number: {str(e)}") from e

    async def update_webhook(
        self,
        twilio_phone_sid: str,
        webhook_url: str,
    ) -> bool:
        """
        Update webhook URL for a phone number.

        Args:
            twilio_phone_sid: Twilio phone number SID
            webhook_url: New webhook URL

        Returns:
            True if successful
        """
        try:
            logger.info(f"Updating webhook for {twilio_phone_sid}")

            self.client.incoming_phone_numbers(twilio_phone_sid).update(
                voice_url=webhook_url,
                voice_method="POST",
                sms_url=webhook_url,
                sms_method="POST",
                status_callback_url=webhook_url,
                status_callback_method="POST",
            )

            logger.info(f"Webhook updated: {twilio_phone_sid}")
            return True

        except Exception as e:
            logger.error(f"Error updating webhook: {str(e)}")
            raise Exception(f"Failed to update webhook: {str(e)}") from e

    def get_phone_number_details(self, twilio_phone_sid: str) -> Dict[str, Any]:
        """
        Get details about a provisioned number.

        Args:
            twilio_phone_sid: Twilio phone number SID

        Returns:
            Phone number details
        """
        try:
            phone_obj = self.client.incoming_phone_numbers(twilio_phone_sid).fetch()

            return {
                "twilio_phone_sid": phone_obj.sid,
                "phone_number": phone_obj.phone_number,
                "friendly_name": phone_obj.friendly_name,
                "status": phone_obj.status,
                "voice_url": phone_obj.voice_url,
                "sms_url": phone_obj.sms_url,
                "date_created": str(phone_obj.date_created),
                "date_updated": str(phone_obj.date_updated),
            }

        except Exception as e:
            logger.error(f"Error getting number details: {str(e)}")
            return None

    def validate_phone_number(self, phone_number: str, country: str = "US") -> bool:
        """
        Validate phone number format.

        Args:
            phone_number: Phone number to validate
            country: Country code

        Returns:
            True if valid format
        """
        import re

        # Basic validation for E.164 format
        pattern = r"^\+?[1-9]\d{1,14}$"
        return bool(re.match(pattern, phone_number.replace(" ", "").replace("-", "")))
