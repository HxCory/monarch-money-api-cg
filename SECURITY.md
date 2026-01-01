# Security Guidelines

## Credential Management

### ✅ What We Do Right

1. **Environment Variables**: Credentials are read from environment variables (`MONARCH_EMAIL`, `MONARCH_PASSWORD`), never hardcoded
2. **Session Persistence**: Using the `monarchmoney` library's built-in session management to avoid repeated logins
3. **No Logging of Credentials**: Password and email are never logged or printed
4. **No Credential Storage in Code**: No API keys, passwords, or tokens in source files

### 🔒 Security Best Practices

#### For Local Development

1. **Use Environment Variables**:
   ```bash
   export MONARCH_EMAIL="your-email@example.com"
   export MONARCH_PASSWORD="your-password"
   ```

2. **Or Use a `.env` file** (recommended):
   - Create a `.env` file in the project root (it's in `.gitignore`)
   - Add your credentials:
     ```
     MONARCH_EMAIL=your-email@example.com
     MONARCH_PASSWORD=your-password
     ```
   - Load it using python-dotenv (optional dependency)

3. **Use Session Caching**:
   - The `monarchmoney` library saves session tokens to avoid repeated logins
   - Session files are stored in `.mm/` directory (excluded from git)
   - Once logged in, you won't need to provide credentials again

#### What NOT to Do

❌ Never commit credentials to git
❌ Never hardcode passwords in Python files
❌ Never share `.env` files
❌ Never commit session files (`.mm/`, `session.pickle`)
❌ Don't log or print sensitive data

### Session File Security

The `monarchmoney` library stores session data in:
- `.mm/` directory (excluded from git via `.gitignore`)

These files contain authentication tokens. **Keep them secure!**

### Checking for Credential Leaks

Before committing, always check:
```bash
# Make sure .env is not tracked
git status

# Search for potential credential leaks
grep -r "password" --exclude-dir=.git --exclude=SECURITY.md .
grep -r "MONARCH_EMAIL" --exclude-dir=.git --exclude=SECURITY.md .
```

### Code Review Checklist

- [ ] No credentials in source code
- [ ] `.env` is in `.gitignore`
- [ ] Session files are in `.gitignore`
- [ ] No credentials in commit messages
- [ ] No logging of sensitive data
- [ ] Environment variables used for all secrets

## Data Privacy

This tool accesses your financial data from Monarch Money:
- Account balances
- Transaction history
- Budget information

**All data stays local** on your machine. We do not:
- Send data to any third-party services
- Store data in cloud services
- Share data with anyone

## Dependencies

We rely on the community-maintained `monarchmoney` library:
- GitHub: https://github.com/hammem/monarchmoney
- This is an unofficial library (use at your own risk)
- Review the library's code if you have security concerns

## Reporting Security Issues

If you find a security vulnerability in this code:
1. Do NOT create a public GitHub issue
2. Contact the repository owner directly
3. Provide details about the vulnerability

## License & Disclaimer

This tool is provided "as is" without warranty. Users are responsible for:
- Securing their own credentials
- Reviewing code before running it
- Understanding the risks of using unofficial APIs
