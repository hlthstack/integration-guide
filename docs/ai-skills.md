# AI coding assistant skills

This repo ships an agent skill, [`skills/hlthstack-api`](../skills/hlthstack-api/SKILL.md),
that teaches AI coding assistants how the hlthstack API works: the base URLs and auth, the
booking, consultation, ePharmacy, wallet and pre-registration flows, webhook verification,
and the field rules that commonly trip people up. With it installed, the assistant reads
the OpenAPI spec instead of guessing endpoints, and asks before it creates, reschedules or
cancels anything.

The skill follows the open [Agent Skills](https://agentskills.io/) format (a folder with a
`SKILL.md`), so the same folder works in Claude Code and OpenAI Codex. For ChatGPT, see
[`skills/chatgpt`](../skills/chatgpt/README.md).

| Tool | Quickest install | Run it |
|---|---|---|
| Claude Code | `claude plugin marketplace add hlthstack/integration-guide` then `claude plugin install hlthstack@hlthstack` | Ask about hlthstack, or type `/hlthstack:hlthstack-api` |
| Codex | In Codex: `$skill-installer install https://github.com/hlthstack/integration-guide/tree/main/skills/hlthstack-api` | Ask about hlthstack, or type `$hlthstack-api` |

## Claude Code

### Option 1: install as a plugin (recommended)

The repo is a Claude Code plugin marketplace. Installing the plugin keeps the skill
up to date with this repo.

```bash
claude plugin marketplace add hlthstack/integration-guide
claude plugin install hlthstack@hlthstack
```

The same commands work inside a Claude Code session:

```text
/plugin marketplace add hlthstack/integration-guide
/plugin install hlthstack@hlthstack
```

Each developer runs these once. To give your whole team the skill without any install
step, use option 2 at project level and commit the folder.

Check it's installed:

```bash
claude plugin details hlthstack@hlthstack
```

Update to the latest version, then restart Claude Code:

```bash
claude plugin marketplace update hlthstack
claude plugin update hlthstack@hlthstack
```

Remove it:

```bash
claude plugin uninstall hlthstack@hlthstack
claude plugin marketplace remove hlthstack
```

### Option 2: copy the skill folder

For all your projects (personal skill):

```bash
rm -rf /tmp/hlthstack-integration-guide
git clone --depth 1 https://github.com/hlthstack/integration-guide.git /tmp/hlthstack-integration-guide
mkdir -p ~/.claude/skills
cp -R /tmp/hlthstack-integration-guide/skills/hlthstack-api ~/.claude/skills/
```

For one project only, run this from the project's root and commit the folder so your team
gets it too:

```bash
rm -rf /tmp/hlthstack-integration-guide
git clone --depth 1 https://github.com/hlthstack/integration-guide.git /tmp/hlthstack-integration-guide
mkdir -p .claude/skills
cp -R /tmp/hlthstack-integration-guide/skills/hlthstack-api .claude/skills/
```

To update, delete the copied `hlthstack-api` folder and copy it again. Claude Code picks up
the change without a restart. If the `skills` folder didn't exist when the session
started, run `/reload-skills`.

### Run it in Claude Code

Start Claude Code in your project and ask about hlthstack. Claude loads the skill on its
own when the request matches:

```bash
claude
```

```text
> Write a Node.js function that books a health checkup on hlthstack staging for one member
```

To load it explicitly, type the skill's slash command, followed by your request:

- installed as a plugin: `/hlthstack:hlthstack-api`
- copied into a skills folder: `/hlthstack-api`

```text
> /hlthstack:hlthstack-api add a webhook endpoint in our Express app that verifies the Signature header
```

Without the interactive UI (for example in a script):

```bash
claude -p "Using the hlthstack API, which header does pre-registration use for its token?"
```

## Codex

Codex reads skills from `.agents/skills` in your repository (from the folder you start
Codex in up to the repository root) and from `~/.agents/skills` for your user.

### Option 1: install with Codex's skill installer

Start Codex and ask its built-in installer to fetch the skill from GitHub:

```bash
codex
```

```text
> $skill-installer install https://github.com/hlthstack/integration-guide/tree/main/skills/hlthstack-api
```

Codex usually picks up a new skill on its own; if `$hlthstack-api` doesn't show up, restart
Codex.

### Option 2: copy the skill folder

For all your projects:

```bash
rm -rf /tmp/hlthstack-integration-guide
git clone --depth 1 https://github.com/hlthstack/integration-guide.git /tmp/hlthstack-integration-guide
mkdir -p ~/.agents/skills
cp -R /tmp/hlthstack-integration-guide/skills/hlthstack-api ~/.agents/skills/
```

For one project only, run this from the repository root and commit the folder:

```bash
rm -rf /tmp/hlthstack-integration-guide
git clone --depth 1 https://github.com/hlthstack/integration-guide.git /tmp/hlthstack-integration-guide
mkdir -p .agents/skills
cp -R /tmp/hlthstack-integration-guide/skills/hlthstack-api .agents/skills/
```

To update, delete the copied `hlthstack-api` folder and copy it again.

### Run it in Codex

Start Codex in your project and ask about hlthstack; Codex uses the skill when the request
matches its description. To pick it explicitly, type `$` and choose `hlthstack-api`, run
`/skills`, or mention it in the prompt:

```text
> $hlthstack-api write a Python script that pre-registers members from members.csv on staging
```

Without the interactive UI:

```bash
codex exec '$hlthstack-api Which header does hlthstack pre-registration use for its token?'
```

Use single quotes so your shell doesn't expand `$hlthstack-api`.

## Credentials and safety

- Keep API credentials in environment variables (for example `HS_USERNAME`,
  `HS_PASSWORD`) or your secret manager. Don't paste them into the chat. The skill tells the
  assistant to read them from the environment and never print or hard-code them.
- The skill uses staging unless you ask for production, and asks before creating,
  rescheduling or cancelling bookings or orders, or changing pre-registered members.
- Both tools ask before running commands that call the API. Review what they run, especially
  against production.

## Example prompts

- "Generate a typed client for the hlthstack consultation endpoints we use."
- "Our `createAppointment` call returns 422; here's the request and response. What's wrong?"
- "Add a webhook handler that verifies the hlthstack `Signature` header and updates our
  appointment status."
- "Write a script that pre-registers the members in `members.csv` on staging and polls until
  the request completes."
- "Move our hlthstack calls from plain `fetch` to the `hlthstack` JS SDK."
