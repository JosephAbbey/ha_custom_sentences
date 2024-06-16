"""Intent handlers."""
import datetime
import random
import typing

import homeassistant.helpers.config_validation as cv
import pytz
import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent


async def async_setup_intents(hass: HomeAssistant) -> None:
    """Set up the custom intent handlers."""
    intent.async_register(hass, ConversationProcessIntentHandler())
    intent.async_register(hass, RandomNumberIntentHandler())
    intent.async_register(hass, CurrentTimeIntentHandler())


class ConversationProcessIntentHandler(intent.IntentHandler):
    """Handle ConversationProcess intents."""

    # Type of intent to handle
    intent_type = "ConversationProcess"

    description = "Processes a prompt or command with a different conversation agent."

    platforms: typing.ClassVar[set[str]] = {"conversation"}

    # Optional. A validation schema for slots
    slot_schema: typing.ClassVar[dict] = {"name": cv.string, "text": cv.string}

    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        """Handle the intent."""
        # Extract the slot values
        slots = intent_obj.slots
        name = slots["name"]["value"]
        text = slots["text"]["value"]

        # Define the constraints for matching the target entity
        constraints = intent.MatchTargetsConstraints(
            name=name, domains=["conversation"], assistant=intent_obj.assistant
        )

        # Match the target entity
        match_result = intent.async_match_targets(intent_obj.hass, constraints)

        if not match_result.is_match:
            response = intent_obj.create_response()
            response.async_set_speech(f"Who is {name}?")
            return response

        # Get the matched entity ID
        matched_entity_id = match_result.states[0].entity_id

        if matched_entity_id == intent_obj.conversation_agent_id:
            response = intent_obj.create_response()
            response.async_set_speech(f"I am {name}!")
            return response

        # Call the conversation.process service and wait for the result
        result = await intent_obj.hass.services.async_call(
            "conversation",
            "process",
            {"text": text, "agent_id": matched_entity_id},
            blocking=True,
            return_response=True,
        )

        # Extract the response text
        response_text = (
            result.get("response", {})
            .get("speech", {})
            .get("plain", {})
            .get("speech", "")
        )

        # Create and return a response
        response = intent_obj.create_response()
        response.async_set_speech(f"{name} says '{response_text}'")
        return response


class RandomNumberIntentHandler(intent.IntentHandler):
    """Handle RandomNumber intents."""

    # Type of intent to handle
    intent_type = "RandomNumber"

    description = "Generate a random number in a range."

    # Optional. A validation schema for slots
    slot_schema: typing.ClassVar[dict] = {
        "from": vol.All(vol.Coerce(int), vol.Range(min=0, max=999999999)),
        "to": vol.All(vol.Coerce(int), vol.Range(min=0, max=999999999)),
    }

    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        """Handle the intent."""
        # Extract the slot values
        slots = intent_obj.slots
        from_value = int(slots["from"]["value"])
        to_value = int(slots["to"]["value"])

        # Generate a random number
        result = random.randint(from_value, to_value)  # noqa: S311

        # Create and return a response
        response = intent_obj.create_response()
        response.async_set_speech(f"{result}")
        return response


class CurrentTimeIntentHandler(intent.IntentHandler):
    """Handle CurrentTime intents."""

    # Type of intent to handle
    intent_type = "CurrentTime"

    description = "Get the current time."

    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        """Handle the intent."""
        # Retrieve the user's timezone from Home Assistant configuration
        user_timezone = intent_obj.hass.config.time_zone

        # Create a timezone object using pytz
        timezone = pytz.timezone(user_timezone)

        # Get the current time in UTC
        utc_now = datetime.datetime.now(datetime.UTC)

        # Convert the current UTC time to the user's timezone
        user_time = utc_now.astimezone(timezone)

        # Format the time as a string
        result = user_time.strftime("%H:%M")

        # Create and return a response
        response = intent_obj.create_response()
        response.async_set_speech(f"The time is {result}")
        return response
