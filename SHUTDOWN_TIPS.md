# How to Shut Down Streamlit Gracefully

## Normal Shutdown

**In the terminal where Streamlit is running:**
- Press `Ctrl+C` once
- Wait a few seconds for it to close
- You should see "Shutting down..." message
- Then return to command prompt

## If Streamlit Hangs

If Streamlit doesn't respond to `Ctrl+C`:

1. **Wait 10-15 seconds** - Sometimes it needs time to clean up
2. **Press `Ctrl+C` again** - Force interrupt
3. **Close the terminal** - As a last resort

## After OAuth Login

The OAuth callback server should automatically shut down after:
- Successful authorization
- Error received
- Timeout (5 minutes)

If it doesn't shut down:
- The server closes automatically after receiving the callback
- If you cancel the login, press `Ctrl+C` in the terminal

## Best Practices

1. **Complete the login process** - Don't interrupt during OAuth
2. **Wait for completion** - Let the process finish naturally
3. **Use `Ctrl+C` once** - Don't spam it, wait for response
4. **Check for hanging processes** - If needed, use Task Manager to kill Python processes

## Troubleshooting

**Streamlit won't shut down:**
- Check if OAuth callback server is still waiting
- Wait for the 5-minute timeout
- Or close the browser tab that's waiting for authorization

**Port 8080 still in use:**
- The server should close automatically
- If not, restart your computer or kill the Python process
