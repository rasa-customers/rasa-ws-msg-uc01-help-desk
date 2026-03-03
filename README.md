# Workshop Use Case 01 - IT Help Desk
An intelligent, Rasa IT support agent that guides users through VPN troubleshooting and automatically creates prioritized ServiceNow tickets when escalation is required.

**Workshop Action Items**
- [ ] Clone/Download this agent locally and run `rasa train`
- [ ] Complete the "happy path" conversation
- [ ] Try a conversation repair pattern
- [ ] Run the e2e tests
- [ ] Launch this agent in Hello Rasa

> [!TIP]
> There is a [**cheatsheet**](#cheatsheet) of Rasa commands at the bottom of this README.

## Clone/Download this agent locally and train your agent
- [ ] Clone or download this agent project locally into your IDE
- [ ] To train your agent, open a terminal window, go inside your project directory, and run `rasa train`
- [ ] The rasa model should train successfully

## Complete the "happy path" conversation
- [ ] Still inside your project directory, run `rasa inspect --debug`
- [ ] The built-in Rasa Inspector should launch and the agent should greet you
- [ ] Try to have the following conversation:

```
BOT: Hello! You have reached the IT Help Desk. How may I help you?
USER: I'm having trouble with my vpn
BOT: Got it. I'll help you troubleshoot that. First, do you see an error message when you try to connect?
USER: yes
BOT: What does the error message say?
USER: VPN authentication failed. Please check your credentials.
BOT: Thanks.
BOT: When was the last time you were able to successfully connect to the VPN?
USER: Yesterday afternoon, around 3pm.
BOT: Are you connected to your home Wi-Fi or another network right now?
USER: wifi
BOT: Based on the error and your answers, it sounds like a credentials sync issue. You can try restarting your computer and reconnecting. If it still fails, we'll escalate it.
BOT: Did the restart help, or do you still need me to open a ticket with IT support?
USER: I’ve already tried restarting. Still not working. I have a meeting in 2 hours and I need to have my VPN working by then
BOT: Okay. Since the error persists and we've ruled out basic causes, I'll go ahead and open a ticket with IT support so they can take a closer look.
BOT: Given the time-sensitivity, I'm treating this as P1-Critical rather than a standard connectivity ticket.
BOT: One moment please...
BOT: I've submitted a support ticket on your behalf. Your case number is INC123456.
BOT: Ticket summary
- Issue type: vpn
- Error message seen: yes
- Error details: VPN authentication failed. Please check your credentials
- Last successful connection: Yesterday afternoon, around 3pm
- Current network: home_wifi
- Case number: INC123456
- Priority: p1_critical
BOT: You'll be contacted shortly by someone from our support team.
BOT: Is there anything else I can help you with?
USER: no
BOT: Okay, I'll be around in case you need further help.
```

## Try a conversation repair pattern
Let's go off the "happy path" a little bit.

Look below at some new messages to send the bot. Rasa handles these "out-of-the-box".
* Notice how we'll answer two questions in one response when talking about the VPN error message. Rasa is smart enough not to ask a question it already got an answer for.
* Rasa can also update past answers you have previously given.

- [ ] Try to have the following conversation:
```diff
BOT: Hello! You have reached the IT Help Desk. How may I help you?
USER: I'm having trouble with my internet
BOT: Understood. Just to confirm, are you having trouble connecting to your VPN, or is it a different internal system like the company portal or another work tool?
USER: vpn issue
BOT: Got it. I'll help you troubleshoot that. First, do you see an error message when you try to connect?
+ USER: Yeah, it says: “VPN authentication failed. Please check your credentials.”
BOT: Thanks.
BOT: When was the last time you were able to successfully connect to the VPN?
USER: Yesterday afternoon, around 3pm.
BOT: Are you connected to your home Wi-Fi or another network right now?
+ USER: actually, the last time I was able to connect was yesterday around 9pm
BOT: Thank you for the clarification! I will update the last successful connection time to yesterday at 9 PM accordingly. If you have any other details to share or questions, feel free to let me know!
BOT: Are you connected to your home Wi-Fi or another network right now?
USER: wifi
...
```

You can 
- [ ] Try to have this conversation:
```diff
BOT: Hello! You have reached the IT Help Desk. How may I help you?
+ USER: I haven't been able to connect with my VPN, since yesterday, through my home wifi
BOT: Got it. I'll help you troubleshoot that. First, do you see an error message when you try to connect?
...
```

## Run the e2e tests
You can run your end-to-end tests using this command: `rasa test e2e tests`

The above command runs all the tests created in the test directory.

You'll find one test didn't work. Why? How can you fix it?

## Launch this agent in Hello Rasa
- [ ] Create a new flow which handles another type of IT issue.

[![Launch on Hello Rasa](https://hello.rasa.com/launch.svg)](https://hello.rasa.com/go?repo=rasa-customers/rasa-ws-msg-uc01-help-desk)  

## Rasa commands

<a name="cheatsheet"></a>
```diff
@@ Cheatsheet @@

+ Train
rasa train
rasa train -c config.yml -d domain

+ Inspect
rasa inspect --debug
rasa inspect --debug --log-file logs.txt

+ Run
rasa run
rasa run actions --debug --auto-reload
rasa run --debug --log-file logs.txt --enable-api --cors "*"

+ Shell
rasa shell --debug

+ E2e
rasa test e2e tests/
```
