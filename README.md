# Custom Sentences

My collection of custom intents for Home Assistant assist. The features of intent scripts suck compared to actual python integrations' intents (and should be fixed or replaced).

Here are my intents:

- `ConversationProcess`
- `RandomNumber`
- `CurrentTime`
- `ReadCalendar`

## Examples (for assist)

For the full syntaxes see [`custom_sentences/en/custom_sentences.yaml`](https://github.com/JosephAbbey/ha_custom_sentences/custom_sentences/en/custom_sentences.yaml).

### `ConversationProcess`

> Ask Gemini to help me stretch my legs
> 
> Ask Gemini help me stretch my legs
> 
> Tell Gemini to help me stretch my legs
> 
> Tell Gemini help me stretch my legs

```
"help me stretch my legs" is sent to Gemini.
```

### `RandomNumber`

> Pick a random number between 1 and 5
> 
> Generate a random number 1 through 5

```
Generates a random integer in the bounds (1 and 5).
```

### `CurrentTime`

> What is the time

```
Returns the time
```

### `ReadCalendar`

> What is on my calendar for today
>
> What is on my calendar for the 21st of June
>
> What is on my calendar after 4pm
>
> What is on my calendar on the 24th before 3pm
>
> What is on my timetable next Thursday at 9:30

```
Returns all calendar events within the timeframe specified.
```

## Installation

Standard HACS installation (you know the drill). Then copy the `custom_sentences` folder to your `config` directory in HomeAssistant.
