## Virtual Environment Logan

### Linux

```bash
source ~/.venvs/nagol-mofia/bin/activate
```

***

# GitHub + VS Code Collaboration Guide

This guide explains how to get the project from GitHub onto your computer, open it in VS Code, create your own branch, make changes, and submit those changes back to the project.

> **Important:** Do NOT work directly on the `main` branch. Always create your own branch first.

---

## 1. Install the Required Software

Before starting, make sure you have:

* [Git](https://git-scm.com/)
* [Visual Studio Code](https://code.visualstudio.com/)
* A GitHub account that has been added as a collaborator on this repository

You can check if Git is installed by opening a terminal and running:

```bash
git --version
```

If you see a version number, Git is installed correctly.

---

# 2. Get the Project From GitHub

Go to the project's GitHub repository.

Click:

**Code → HTTPS → Copy**

You will get a URL that looks something like:

```text
https://github.com/USERNAME/REPOSITORY.git
```

Keep that URL copied.

---

# 3. Open VS Code

Open Visual Studio Code.

Then open the terminal:

**Terminal → New Terminal**

You can also use the keyboard shortcut:

```text
Ctrl + `
```

---

# 4. Choose Where You Want the Project

In the terminal, navigate to the folder where you want to keep the project.

For example:

```bash
cd Desktop
```

Or:

```bash
cd Documents
```

Or:

```bash
cd projects
```

You can check what folder you're currently in with:

```bash
pwd
```

---

# 5. Clone the Repository

Now download the project from GitHub by running:

```bash
git clone https://github.com/USERNAME/REPOSITORY.git
```

Replace the URL above with the URL you copied from GitHub.

For example:

```bash
git clone https://github.com/john/project.git
```

This creates a folder containing the entire project.

---

# 6. Go Into the Project Folder

Run:

```bash
cd REPOSITORY
```

Replace `REPOSITORY` with the actual name of the project.

For example:

```bash
cd project
```

---

# 7. Open the Project in VS Code

Run:

```bash
code .
```

The project should now open in VS Code.

You should see all of the project files on the left side of VS Code.

---

# 8. Make Sure You Have the Latest Version

Before starting any work, make sure you're on the `main` branch:

```bash
git checkout main
```

Then download the latest changes from GitHub:

```bash
git pull origin main
```

This makes sure you're starting with the most recent version of the project.

---

# 9. Create Your Own Branch

DO NOT make your changes directly on `main`.

Create a new branch for whatever you're working on.

For example, if you're working on the login page:

```bash
git checkout -b login-page
```

You can name the branch whatever makes sense.

Examples:

```bash
git checkout -b login-page
```

```bash
git checkout -b fix-navbar
```

```bash
git checkout -b add-homepage
```

```bash
git checkout -b user-profile
```

You can check which branch you're currently on with:

```bash
git branch
```

You should see something like:

```text
* login-page
  main
```

The `*` shows which branch you're currently using.

---

# 10. Start Working

Now you can work on the project normally in VS Code.

You can:

* Modify existing files
* Create new files
* Delete files
* Add features
* Fix bugs
* Test your changes

Your changes are currently only on your local computer and your branch.

They have NOT been added to `main`.

---

# 11. Check Your Changes

When you're ready to see what you've changed, run:

```bash
git status
```

This shows which files have been changed.

You can see the actual changes by running:

```bash
git diff
```

It's a good idea to review your changes before committing them.

---

# 12. Add Your Changes

When you're happy with your work, run:

```bash
git add .
```

This tells Git that you want to include your changes in the next commit.

---

# 13. Commit Your Changes

Create a commit:

```bash
git commit -m "Describe what you changed"
```

For example:

```bash
git commit -m "Add login page"
```

Or:

```bash
git commit -m "Fix navigation bar"
```

Or:

```bash
git commit -m "Add user profile page"
```

A commit is basically a saved checkpoint of your work.

---

# 14. Push Your Branch to GitHub

Now upload your branch to GitHub:

```bash
git push -u origin YOUR-BRANCH-NAME
```

For example:

```bash
git push -u origin login-page
```

This uploads your branch to GitHub.

**This does NOT change `main`.**

---

# 15. Create a Pull Request

Go back to the project's GitHub page.

After pushing your branch, GitHub will usually show a button saying:

**Compare & pull request**

Click it.

You should see something similar to:

```text
login-page → main
```

This means you're asking to merge your `login-page` branch into `main`.

Give the pull request a clear title.

For example:

```text
Add login page
```

Then describe what you changed.

For example:

```text
Added the login page UI and connected the login form to the existing authentication system.
```

Then click:

**Create pull request**

---

# 16. Wait for the Pull Request to Be Reviewed

The repository owner will review your changes.

They may:

* Approve the changes
* Ask you to make changes
* Leave comments
* Request modifications

If changes are requested, you do NOT need to create another pull request.

Simply make the requested changes on the same branch.

Then:

```bash
git add .
git commit -m "Address pull request feedback"
git push
```

The existing pull request will automatically update.

---

# 17. After the Pull Request Is Approved

Once the changes are approved, the repository owner can merge the pull request into `main`.

After it is merged, your work is officially part of the main project.

---

# 18. Starting Your Next Task

After your previous branch has been merged, DO NOT immediately start working on that same branch.

First, switch back to `main`:

```bash
git checkout main
```

Then get the newest version:

```bash
git pull origin main
```

Now create a new branch:

```bash
git checkout -b new-feature
```

For example:

```bash
git checkout -b settings-page
```

Then start working.

---

# The Normal Workflow

Once you understand Git, your normal workflow will look like this:

```text
1. Update main
       ↓
2. Create a new branch
       ↓
3. Work in VS Code
       ↓
4. Check your changes
       ↓
5. git add .
       ↓
6. git commit
       ↓
7. git push
       ↓
8. Create Pull Request
       ↓
9. Get your code reviewed
       ↓
10. Fix anything requested
       ↓
11. Pull Request gets merged
       ↓
12. Start the next task
```

---

# Quick Command Reference

## First Time Setting Up the Project

```bash
git clone <repository-url>
cd <repository-folder>
code .
```

## Before Starting Work

```bash
git checkout main
git pull origin main
```

## Create a New Branch

```bash
git checkout -b <branch-name>
```

## Check Your Work

```bash
git status
git diff
```

## Save Your Work

```bash
git add .
git commit -m "Describe your changes"
```

## Upload Your Branch

First time:

```bash
git push -u origin <branch-name>
```

After that:

```bash
git push
```

---

# Example: Complete Feature

Let's say you're asked to add a profile page.

First:

```bash
git checkout main
git pull origin main
```

Create a branch:

```bash
git checkout -b profile-page
```

Work on the profile page in VS Code.

Then:

```bash
git status
```

Review your changes:

```bash
git diff
```

Add them:

```bash
git add .
```

Commit:

```bash
git commit -m "Add profile page"
```

Push:

```bash
git push -u origin profile-page
```

Then go to GitHub and create a pull request:

```text
profile-page → main
```

Wait for the code review.

If changes are requested, make them and run:

```bash
git add .
git commit -m "Update profile page"
git push
```

The pull request will automatically update.

---

# Important Rules

### 1. Don't work directly on `main`

Always create a branch:

```bash
git checkout -b my-feature
```

### 2. Pull before starting new work

Always make sure `main` is up to date:

```bash
git checkout main
git pull origin main
```

### 3. Keep your commits meaningful

Instead of:

```bash
git commit -m "stuff"
```

Use:

```bash
git commit -m "Add profile page"
```

### 4. Don't panic if something goes wrong

Git can be confusing at first.

If you aren't sure what a command will do, **stop before running it** and ask.

Do not randomly run commands like:

```bash
git reset --hard
```

unless you know exactly what they do, because they can delete local changes.

---

# The Three Commands to Remember

If you forget everything else, remember this basic cycle:

```bash
git add .
git commit -m "Describe my changes"
git push
```

Those commands save your work and upload it to your branch.

Then create/update the Pull Request on GitHub.

---

# Final Goal

The goal is:

```text
                 GitHub
                    │
                    │ clone
                    ↓
              Your Computer
                    │
                    ↓
                 VS Code
                    │
                    │
             Create a branch
                    │
                    ↓
              Make changes
                    │
                    ↓
                 Commit
                    │
                    ↓
                  Push
                    │
                    ↓
              GitHub Branch
                    │
                    ↓
             Pull Request
                    │
                    ↓
                  Review
                    │
                    ↓
              Merge → main
```

**You work on your branch.
You push your branch.
You create a pull request.
The changes get reviewed.
Then the pull request gets merged into `main`.**

