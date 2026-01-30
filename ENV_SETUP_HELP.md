# Environment Variables Setup Help

## Issue
The script is not finding your API credentials in the `.env` file.

## Quick Fix

**1. Check your `.env` file exists and has the right variable names:**

Your `.env` file should have **ONE** of these sets:

**Option 1 (Recommended):**
```env
VITE_ENISCOPE_API_URL=https://core.eniscope.com
VITE_ENISCOPE_API_KEY=your_api_key_here
VITE_ENISCOPE_EMAIL=your_email_here
VITE_ENISCOPE_PASSWORD=your_password_here
```

**Option 2:**
```env
VITE_BEST_ENERGY_API_URL=https://core.eniscope.com
VITE_BEST_ENERGY_API_KEY=your_api_key_here
VITE_ENISCOPE_EMAIL=your_email_here
VITE_ENISCOPE_PASSWORD=your_password_here
```

**Option 3:**
```env
ENISCOPE_API_URL=https://core.eniscope.com
ENISCOPE_API_KEY=your_api_key_here
ENISCOPE_EMAIL=your_email_here
ENISCOPE_PASSWORD=your_password_here
```

**2. Verify your `.env` file format:**

- ✅ No spaces around the `=` sign: `KEY=value` (not `KEY = value`)
- ✅ No quotes needed (but they're okay): `KEY=value` or `KEY="value"`
- ✅ One variable per line
- ✅ No blank lines between variables
- ✅ File should be named exactly `.env` (with the dot at the start)

**3. Check file location:**
The `.env` file should be in the project root:
```
/Users/sargo/argo-energy-solutions/.env
```

**4. Test your variables:**

Run with debug mode to see what's being found:
```bash
DEBUG=1 npm run ingest:full
```

This will show which variables are set and which are missing.

## Common Issues

### Issue: "injecting env (0) from .env"
- **Cause:** `.env` file is empty or has no valid variables
- **Fix:** Add the variables listed above

### Issue: "Missing API_KEY"
- **Cause:** Variable name doesn't match exactly
- **Fix:** Use one of the variable names listed above (case-sensitive!)

### Issue: Variables not loading
- **Cause:** `.env` file might have syntax errors
- **Fix:** 
  1. Check for typos in variable names
  2. Make sure there are no spaces around `=`
  3. Make sure each line has a variable

## Example `.env` file

Here's a complete example (replace with your actual values):

```env
# Eniscope API Configuration
VITE_ENISCOPE_API_URL=https://core.eniscope.com
VITE_ENISCOPE_API_KEY=abc123xyz789
VITE_ENISCOPE_EMAIL=your.email@example.com
VITE_ENISCOPE_PASSWORD=your_password_here
```

**Important:** Replace the example values with your actual credentials!

## Verify It Works

After updating your `.env` file, test it:

```bash
DEBUG=1 npm run ingest:full
```

You should see:
```
🔍 Environment variables check:
   VITE_ENISCOPE_API_KEY: ✓ Set (abc123xy...)
   VITE_ENISCOPE_EMAIL: ✓ Set
   VITE_ENISCOPE_PASSWORD: ✓ Set
```

If you see all ✓ marks, you're good to go! 🎉

## Still Not Working?

1. **Double-check the file path:** The script looks for `.env` in `/Users/sargo/argo-energy-solutions/.env`
2. **Check file permissions:** Make sure the file is readable
3. **Try a different variable name:** Use `VITE_BEST_ENERGY_API_KEY` instead of `VITE_ENISCOPE_API_KEY` if that's what your other scripts use
4. **Check for hidden characters:** Sometimes copying/pasting can add invisible characters

---

**Need help?** Check which variable names your other working scripts use. Look at `scripts/wilson-center-analysis.js` or `scripts/analyze-energy-data.js` to see what they expect.
