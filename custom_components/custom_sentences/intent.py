"""Intent handlers."""

import datetime
import logging
import random
import typing

import homeassistant.helpers.config_validation as cv
import pytz
import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent

_LOGGER = logging.getLogger(__name__)


async def async_setup_intents(hass: HomeAssistant) -> None:
    """Set up the custom intent handlers."""
    intent.async_register(hass, ConversationProcessIntentHandler())
    intent.async_register(hass, RandomNumberIntentHandler())
    intent.async_register(hass, CurrentTimeIntentHandler())
    intent.async_register(hass, ReadCalendarIntentHandler())


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


class ReadCalendarIntentHandler(intent.IntentHandler):
    """Handle ReadCalendar intents."""

    # Type of intent to handle
    intent_type = "ReadCalendar"

    description = "Read events from the user's calendar."

    platforms: typing.ClassVar[set[str]] = {"calendar"}

    slot_schema: typing.ClassVar[dict] = {
        vol.Required("name", description="The calendar entity to read."): cv.string,
        vol.Optional(
            "relative_day", description="Either 'today' or 'tomorrow'."
        ): cv.string,
        vol.Optional(
            "this",
            description="Either 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'weekend', or 'week'.",  # noqa: E501
        ): cv.string,
        vol.Optional(
            "next",
            description="Either 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'weekend', or 'week'.",  # noqa: E501
        ): cv.string,
        vol.Optional("day", description="Day of the month."): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=31)
        ),
        vol.Optional("month", description="Month as value between 1 and 12."): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=12)
        ),
        vol.Optional(
            "before_at_after", description="Either 'before', 'at', or 'after'"
        ): cv.string,
        vol.Optional("hour", description="Hour of the day."): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=23)
        ),
        vol.Optional("minute", description="Minute of the hour."): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=59)
        ),
        vol.Optional("ampm", description="Either 'am' or 'pm'"): cv.string,
    }

    def _relative(  # noqa: PLR0913
        self,
        relative: str,
        timezone: pytz.timezone,
        start_date_time: datetime.datetime,
        end_date_time: datetime.datetime,
        add_delta: datetime.timedelta = datetime.timedelta(),
    ) -> tuple[datetime.datetime, datetime.datetime]:
        """Calculate the start and end date times for a relative time period."""
        match relative:
            case "monday":
                start_date_time = (
                    datetime.datetime.now(timezone).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                    - datetime.timedelta(days=start_date_time.weekday())
                    + add_delta
                )
                end_date_time = start_date_time + datetime.timedelta(days=1)
            case "tuesday":
                start_date_time = (
                    datetime.datetime.now(timezone).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                    + datetime.timedelta(days=1 - start_date_time.weekday())
                    + add_delta
                )
                end_date_time = start_date_time + datetime.timedelta(days=1)
            case "wednesday":
                start_date_time = (
                    datetime.datetime.now(timezone).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                    + datetime.timedelta(days=2 - start_date_time.weekday())
                    + add_delta
                )
                end_date_time = start_date_time + datetime.timedelta(days=1)
            case "thursday":
                start_date_time = (
                    datetime.datetime.now(timezone).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                    + datetime.timedelta(days=3 - start_date_time.weekday())
                    + add_delta
                )
                end_date_time = start_date_time + datetime.timedelta(days=1)
            case "friday":
                start_date_time = (
                    datetime.datetime.now(timezone).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                    + datetime.timedelta(days=4 - start_date_time.weekday())
                    + add_delta
                )
                end_date_time = start_date_time + datetime.timedelta(days=1)
            case "saturday":
                start_date_time = (
                    datetime.datetime.now(timezone).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                    + datetime.timedelta(days=5 - start_date_time.weekday())
                    + add_delta
                )
                end_date_time = start_date_time + datetime.timedelta(days=1)
            case "sunday":
                start_date_time = (
                    datetime.datetime.now(timezone).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                    + datetime.timedelta(days=6 - start_date_time.weekday())
                    + add_delta
                )
                end_date_time = start_date_time + datetime.timedelta(days=1)
            case "weekend":
                start_date_time = (
                    datetime.datetime.now(timezone).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                    + datetime.timedelta(days=5 - start_date_time.weekday())
                    + add_delta
                )
                end_date_time = start_date_time + datetime.timedelta(days=2)
            case "week":
                start_date_time = (
                    datetime.datetime.now(timezone).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                    - datetime.timedelta(days=start_date_time.weekday())
                    + add_delta
                )
                end_date_time = start_date_time + datetime.timedelta(days=7)
        return start_date_time, end_date_time

    async def async_handle(  # noqa: PLR0915, PLR0912, C901
        self, intent_obj: intent.Intent
    ) -> intent.IntentResponse:
        """Handle the intent."""
        # Validate slots
        slots = self.async_validate_slots(intent_obj.slots)

        # Extract the slot values
        name = slots["name"]["value"]
        relative_day = slots.get("relative_day", {}).get("value", None)
        this = slots.get("this", {}).get("value", None)
        _next = slots.get("next", {}).get("value", None)
        day = slots.get("day", {}).get("value", None)
        if day is not None:
            day = int(day)
        month = slots.get("month", {}).get("value", None)
        if month is not None:
            month = int(month)
        before_at_after = slots.get("before_at_after", {}).get("value", None)
        hour = slots.get("hour", {}).get("value", None)
        if hour is not None:
            hour = int(hour)
        minute = slots.get("minute", {}).get("value", None)
        if minute is not None:
            minute = int(minute)
        ampm = slots.get("ampm", {}).get("value", None)

        # Match calendar
        constraints = intent.MatchTargetsConstraints(
            name=name, domains=["calendar"], assistant=intent_obj.assistant
        )

        match_result = intent.async_match_targets(intent_obj.hass, constraints)

        if not match_result.is_match:
            response = intent_obj.create_response()
            response.async_set_speech(f"Unknown calendar '{name}'.")
            return response

        matched_entity_id = match_result.states[0].entity_id

        # Get timezone from Home Assistant configuration
        user_timezone = intent_obj.hass.config.time_zone

        # Create a timezone object using pytz
        timezone = pytz.timezone(user_timezone)

        # Use ampm
        if ampm == "pm" and hour < 12:  # noqa: PLR2004
            hour += 12

        # Calculate the start and end date times
        start_date_time = datetime.datetime.now(timezone)
        end_date_time = start_date_time.replace(hour=23, minute=59, second=59)
        match relative_day:
            case "today":
                end_date_time = start_date_time.replace(hour=23, minute=59, second=59)
            case "tomorrow":
                start_date_time = start_date_time.replace(
                    hour=0, minute=0, second=0
                ) + datetime.timedelta(days=1)
                end_date_time = start_date_time.replace(hour=23, minute=59, second=59)
        if this is not None:
            start_date_time, end_date_time = self._relative(
                this, timezone, start_date_time, end_date_time
            )
        if _next is not None:
            start_date_time, end_date_time = self._relative(
                _next,
                timezone,
                start_date_time,
                end_date_time,
                datetime.timedelta(weeks=1),
            )
        if day is not None:
            if month is not None:
                start_date_time = start_date_time.replace(month=month)
            start_date_time = start_date_time.replace(day=day)
            end_date_time = start_date_time + datetime.timedelta(days=1)
        match before_at_after:
            case "before":
                end_date_time = end_date_time.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )
            case "at":
                start_date_time = start_date_time.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )
                end_date_time = start_date_time
            case "after":
                end_date_time = end_date_time.replace(hour=23, minute=59, second=59)
                if hour is not None:
                    start_date_time = start_date_time.replace(
                        hour=hour, minute=minute, second=0, microsecond=0
                    )

        # Ensure start_date_time is after now
        start_date_time = max(start_date_time, datetime.datetime.now(timezone))

        # Call the calendar.get_events service and wait for the result
        result = await intent_obj.hass.services.async_call(
            "calendar",
            "get_events",
            {
                "entity_id": matched_entity_id,
                "start_date_time": start_date_time,
                "end_date_time": end_date_time,
            },
            blocking=True,
            return_response=True,
        )
        events = result.get(matched_entity_id, {}).get("events", None)

        # Generate response
        if events is None or len(events) == 0:
            response = intent_obj.create_response()
            response.async_set_speech("There are no events.")
            return response

        inc_day = (end_date_time - start_date_time) >= datetime.timedelta(days=1)

        today = datetime.datetime.now(timezone).date()
        tomorrow = datetime.datetime.now(timezone).date() + datetime.timedelta(days=1)

        response = intent_obj.create_response()
        text = "The events are: "
        for event in events:
            start = datetime.datetime.fromisoformat(event["start"])
            start_date = start.date()
            end = datetime.datetime.fromisoformat(event["end"])
            length = end - start
            if length == datetime.timedelta(days=1):
                time = "all day"
                if inc_day:
                    if start_date == today:
                        time = "Today"
                    elif start_date == tomorrow:
                        time = "Tomorrow"
                    else:
                        time = start.strftime("on %A")
            elif length > datetime.timedelta(days=1):
                time = "continued"
                if inc_day:
                    if start_date < today:
                        time = end.strftime("ending on %A")
                    elif start_date == today:
                        time = "starting today"
                    elif start_date == tomorrow:
                        time = "starting tomorrow"
                    else:
                        time = start.strftime("starting on %A")
            else:
                time = start.strftime("at %-I:%M %p")
                if inc_day:
                    if start_date == today:
                        time = "Today " + time
                    elif start_date == tomorrow:
                        time = "Tomorrow " + time
                    else:
                        time = start.strftime("on %A ") + time
            text += f"{event['summary']} {time}, "
        text = text[:-2] + "."
        response.async_set_speech(text)
        return response
