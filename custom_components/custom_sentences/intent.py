"""Intent handlers."""

import typing

import homeassistant.helpers.config_validation as cv
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent


async def async_setup_intents(hass: HomeAssistant) -> None:
    """Set up the custom intent handlers."""
    intent.async_register(hass, ConversationProcessIntentHandler())


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
