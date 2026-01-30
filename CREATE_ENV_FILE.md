# How to Create Your .env File

## Step-by-Step Instructions

### Step 1: Create the File

1. In your project root directory (`/Users/sargo/argo-energy-solutions/`), create a new file named `.env`
2. Make sure it's exactly named `.env` (with the dot at the beginning, no extension)

### Step 2: Add the Following Content

Copy and paste this into your `.env` file:

```env
# Best.Energy API Configuration
# Replace the values below with your actual API credentials

# Your Best.Energy API base URL
# Example: https://api.best.energy or https://api.bestenergy.com
VITE_BEST_ENERGY_API_URL=https://api.best.energy

# Your Best.Energy API key or token
# Replace 'your_api_key_here' with your actual API key
VITE_BEST_ENERGY_API_KEY=your_api_key_here

# API request timeout in milliseconds (optional, default is 30000)
VITE_API_TIMEOUT=30000
```

### Step 3: Replace the Placeholder Values

**Important:** You need to replace `your_api_key_here` with your actual Best.Energy API key!

1. Find your API key from Best.Energy (check your account or documentation)
2. Replace `your_api_key_here` with your actual key
3. If your API URL is different, update `VITE_BEST_ENERGY_API_URL` as well

### Step 4: Save the File

Save the `.env` file in the root directory of your project (same level as `package.json`)

### Step 5: Restart Your Dev Server

**Important:** After creating or modifying the `.env` file, you MUST restart your development server:

1. Stop your current dev server (Ctrl+C or Cmd+C)
2. Run `npm run dev` again
3. The new environment variables will now be loaded

---

## Example .env File

Here's what your `.env` file should look like (with real values):

```env
VITE_BEST_ENERGY_API_URL=https://api.best.energy
VITE_BEST_ENERGY_API_KEY=sk_live_abc123xyz789
VITE_API_TIMEOUT=30000
```

---

## Creating the File in Different Editors

### VS Code / Cursor
1. Right-click in the file explorer (in the root directory)
2. Select "New File"
3. Name it `.env` (make sure it starts with a dot)
4. Paste the content above
5. Save the file

### Terminal / Command Line
```bash
# Navigate to your project root
cd /Users/sargo/argo-energy-solutions

# Create the .env file
touch .env

# Open it in your editor
code .env
# or
nano .env
```

Then paste the content and save.

### macOS Finder
1. Open Finder and navigate to your project folder
2. Press `Cmd + Shift + .` to show hidden files
3. Create a new file named `.env`
4. Open it in a text editor and paste the content

---

## Verify Your .env File is Working

1. Make sure the file is in the root directory (same folder as `package.json`)
2. Restart your dev server
3. Navigate to `/api-test` in your app
4. Check the browser console - you should see API requests being made

---

## Security Notes

- ✅ The `.env` file is already added to `.gitignore` - it won't be committed to git
- ✅ Never share your `.env` file or API keys publicly
- ✅ Each developer should have their own `.env` file
- ✅ Use `.env.example` (which is safe to commit) as a template

---

## Troubleshooting

### File Not Found Error
- Make sure the file is named exactly `.env` (with the dot)
- Make sure it's in the root directory (not in a subfolder)
- Make sure there are no spaces in the filename

### Variables Not Loading
- Restart your dev server after creating/modifying `.env`
- Make sure variable names start with `VITE_` (required for Vite)
- Check for typos in variable names
- Make sure there are no quotes around the values (unless needed)

### Still Having Issues?
- Check the browser console for errors
- Verify the file path is correct
- Make sure you saved the file
- Try restarting your editor/IDE



