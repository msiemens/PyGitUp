# Security Policy

## Supported Versions

| Version                 | Supported          |
| ----------------------- | ------------------ |
| Latest PyGitUp release  | :white_check_mark:  |
| All prior versions      | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you believe you've found a security vulnerability in PyGitUp, please report it by using GitHub's [private vulnerability reporting feature](https://github.com/msiemens/PyGitUp/security/advisories/new).

Please include:

- A clear description of the vulnerability
- A realistic attack scenario demonstrating how untrusted external input leads to the security impact
- Steps to reproduce
- Your assessment of severity and impact

I aim to respond within 7 days and will work with you on a fix and coordinated disclosure on a mutually agreed timeline if the issue is valid. 

## Scope:  What Constitutes a PyGitUp Vulnerability

This security policy applies to the PyGitUp package as distributed via [PyPI](https://pypi.org/project/git-up/) and the source code in the [msiemens/PyGitUp](https://github.com/msiemens/PyGitUp) repository.

### Explicitly Out of Scope

Security reports must demonstrate that PyGitUp itself is the source of the vulnerability, not simply present in a vulnerable scenario.

The following are **not** considered PyGitUp vulnerabilities:

- **Vulnerabilities in dependencies.** Please report these to the respective projects.  

- **Vulnerabilities in Git itself.** PyGitUp relies on Git; vulnerabilities in Git should be reported to the Git project.

- **Local access attacks.** If an attacker has local access to modify `.gitconfig` or `.git/config` files, this represents a broader system compromise, not a PyGitUp vulnerability.

- **Social engineering attacks.** Attacks that rely on tricking users into performing actions are out of scope.  