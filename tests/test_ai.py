from ai_labeler.ai import labeling_workflow
from ai_labeler.github import PullRequest, Issue, Label


def test_bug_with_reproduction_steps():
    labels = [
        Label(
            name="bug",
            description="Something isn't working",
            instructions="Only apply this label when there's clear reproduction steps",
        ),
        Label(name="enhancement", description="New feature or request"),
    ]

    pr = PullRequest(
        title="Fix database connection timeout",
        body="""This PR fixes a critical bug where database connections would timeout.
        
        Steps to reproduce:
        1. Run the server with default settings
        2. Wait 30 seconds
        3. Observe connection errors in logs
        
        Fix: Increased timeout and added connection pooling.""",
        files={"src/database.py": "content here"},
        author="marvin",
    )

    result = labeling_workflow(item=pr, labels=labels)
    assert "bug" in result
    assert "enhancement" not in result


def test_bug_without_reproduction_steps():
    labels = [
        Label(
            name="bug",
            description="Something isn't working.",
            instructions="Only apply this label if the user provided a Python MRE",
        )
    ]

    pr = Issue(
        title="Timeout issue",
        body="The database timed out",
        author="marvin",
    )

    result = labeling_workflow(item=pr, labels=labels)
    assert "bug" not in result


def test_dependency_updates():
    labels = [
        Label(
            name="dependencies",
            description="Updates to dependencies",
            instructions="Always apply this label to PRs that modify package.json, requirements.txt, or similar files",
        ),
        Label(name="documentation", description="Documentation updates"),
    ]

    pr = PullRequest(
        title="Update pytest to 7.4.0",
        body="Routine dependency update to get latest pytest features",
        files={
            "requirements.txt": "pytest==7.4.0\nrequests==2.31.0",
            "test_requirements.txt": "pytest==7.4.0",
        },
        author="marvin",
    )

    result = labeling_workflow(item=pr, labels=labels)
    assert "dependencies" in result
    assert "documentation" not in result


def test_documentation_changes():
    labels = [
        Label(name="documentation", description="Documentation updates"),
        Label(name="bug", description="Something isn't working"),
    ]

    pr = PullRequest(
        title="Improve installation docs",
        body="Added clearer installation instructions",
        files={"README.md": "content", "docs/install.md": "content"},
        author="marvin",
    )

    result = labeling_workflow(item=pr, labels=labels)
    assert "documentation" in result
    assert "bug" not in result


def test_never_apply_label():
    labels = [
        Label(
            name="do-not-merge",
            description="This PR should not be merged yet",
            instructions="Never apply this label automatically!",
        ),
        Label(name="bug", description="Something isn't working"),
    ]

    pr = PullRequest(
        title="WIP: Database fixes",
        body="Work in progress - DO NOT MERGE",
        files={"src/db.py": "content"},
        author="marvin",
    )

    result = labeling_workflow(item=pr, labels=labels)
    assert "do-not-merge" not in result


def test_feature_request():
    labels = [
        Label(name="enhancement", description="New feature or request"),
        Label(name="bug", description="Something isn't working"),
    ]

    issue = Issue(
        title="Add dark mode support",
        body="It would be great to have dark mode support for better accessibility",
        author="marvin",
    )

    result = labeling_workflow(item=issue, labels=labels)
    assert "enhancement" in result
    assert "bug" not in result


def test_multiple_valid_labels():
    labels = [
        Label(
            name="dependencies",
            description="Updates to dependencies",
            instructions="Always apply this label to PRs that modify package.json, requirements.txt, or similar files",
        ),
        Label(name="documentation", description="Documentation updates"),
    ]

    pr = PullRequest(
        title="Update dependencies and docs",
        body="Updated dependencies and improved their documentation",
        files={"requirements.txt": "new deps", "docs/dependencies.md": "updated docs"},
        author="marvin",
    )

    result = labeling_workflow(item=pr, labels=labels)
    assert "dependencies" in result
    assert "documentation" in result


def test_custom_instructions_override():
    labels = [
        Label(name="bug", description="Something isn't working"),
        Label(name="enhancement", description="New feature or request"),
    ]

    issue = Issue(
        title="System crash on startup",
        body="Sometimes the system crashes on startup",  # No clear reproduction steps
        author="marvin",
    )

    result = labeling_workflow(
        item=issue,
        labels=labels,
        instructions="Be extremely conservative with bug labels - only apply if there are clear steps to reproduce",
    )
    assert "bug" not in result


def test_security_label_with_instructions():
    labels = [
        Label(
            name="security",
            description="Security-related changes",
            instructions="Apply this label if the PR mentions security fixes, CVEs, or modifies security-critical code",
        ),
    ]

    pr = PullRequest(
        title="Fix CVE-2024-1234",
        body="This PR addresses CVE-2024-1234 by updating our JWT handling",
        files={"src/auth.py": "content"},
        author="marvin",
    )

    result = labeling_workflow(item=pr, labels=labels)
    assert "security" in result


def test_complex_feature_pr():
    labels = [
        Label(name="enhancement", description="New feature or request"),
        Label(
            name="breaking-change",
            description="Introduces breaking changes",
            instructions="Apply when PR includes API changes that aren't backward compatible",
        ),
        Label(
            name="needs-tests",
            description="More tests needed",
            instructions="Apply if the PR modifies logic but doesn't include corresponding test updates",
        ),
        Label(name="documentation", description="Documentation updates"),
        Label(
            name="performance",
            description="Performance improvements",
            instructions="Apply when changes are reported to drive significant performance gains",
        ),
    ]

    pr = PullRequest(
        title="Add async support to database operations",
        body="""Major enhancement to add async/await support to all database operations.

        Key changes:
        - Convert all database operations to use asyncio
        - Add connection pooling for better performance
        - Update all public APIs to be async-first
        - Add new AsyncDatabaseClient class
        - Deprecate old synchronous methods
        
        Breaking changes:
        - DatabaseClient methods now return awaitables
        - Removed sync_query method in favor of async_query
        - Connection configuration now requires pool_size parameter
        
        Performance improvements:
        - Connection pooling reduces connection overhead by ~40%
        - Batch operations now process 3x faster in benchmarks
        
        Example usage:        ```python
        client = AsyncDatabaseClient()
        results = await client.query("SELECT * FROM users")        ```
        """,
        files={
            "src/database.py": """
                import asyncio
                from typing import Optional
                
                class AsyncDatabaseClient:
                    async def query(self):
                        pass
                    
                    async def batch_query(self):
                        pass
            """,
            "tests/test_database.py": """
                import pytest
                import asyncio
                
                async def test_async_query():
                    client = AsyncDatabaseClient()
                    result = await client.query()
                    assert result is not None
            """,
            "docs/async-migration.md": "# Migrating to Async API\n\nGuide for updating your code... <truncated>",
            "examples/async_usage.py": "# Example async usage\n\nasync def main():\n    ... <truncated>",
            "CHANGELOG.md": "# 2.0.0\n\n- Added async support\n- Breaking: removed sync methods",
        },
        author="marvin",
    )

    result = labeling_workflow(item=pr, labels=labels)

    # Major feature addition
    assert "enhancement" in result

    # Changes public API
    assert "breaking-change" in result

    # Includes corresponding test updates
    assert "needs-tests" not in result

    # Includes migration guide and examples
    assert "documentation" in result

    # Mentions specific performance improvements with benchmarks
    assert "performance" in result


def test_codeowners_based_labels():
    labels = [
        Label(
            name="frontend-review",
            description="Needs review from frontend team",
            instructions="""
            Apply when changes touch frontend code:
            - Files in frontend/ or ui/ directories
            - Files owned by @frontend-team in CODEOWNERS
            - Changes to CSS, JavaScript, or React components
            """,
        ),
        Label(
            name="backend-review",
            description="Needs review from backend team",
            instructions="""
            Apply for changes to backend systems:
            - Files in backend/ or api/ directories
            - Files owned by @backend-team in CODEOWNERS
            - Database or API changes
            """,
        ),
    ]

    context_files = {
        ".github/CODEOWNERS": """
        # Frontend
        /frontend/**  @frontend-team
        *.tsx        @frontend-team
        *.css        @frontend-team
        
        # Backend
        /backend/**  @backend-team
        /api/**      @backend-team
        *.sql        @backend-team
        """
    }

    pr = PullRequest(
        title="Update user profile UI and API",
        body="Added new fields to user profile and corresponding API endpoints",
        files={
            "frontend/components/UserProfile.tsx": "component code...",
            "frontend/styles/profile.css": "styling...",
            "backend/api/user_profile.py": "api code...",
            "backend/db/migrations/add_profile_fields.sql": "migration...",
        },
        author="marvin",
    )

    result = labeling_workflow(
        item=pr,
        labels=labels,
        context_files=context_files,
    )

    assert "frontend-review" in result
    assert "backend-review" in result


def test_security_review_routing():
    labels = [
        Label(
            name="security-review",
            description="Needs security team review",
            instructions="""
            Apply if changes involve security-critical code:
            - Authentication/authorization code
            - Files in security/ or auth/ directories
            - Files owned by @security-team in CODEOWNERS
            - Cryptographic operations
            - Environment variables
            """,
        ),
        Label(
            name="high-priority",
            description="Needs immediate attention",
            instructions="""
            Apply to urgent changes, including:
            - Security fixes
            - Production hotfixes
            - Critical path changes
            """,
        ),
    ]

    context_files = {
        ".github/CODEOWNERS": """
        # Security-critical files
        /security/**     @security-team
        /auth/**        @security-team
        **/security.*   @security-team
        **/auth.*       @security-team
        *.key           @security-team
        """,
        ".github/SECURITY.md": """
        # Security Policy
        
        All changes to authentication, authorization, or cryptographic
        operations must be reviewed by the security team.
        """,
    }

    pr = PullRequest(
        title="Update JWT handling and add rate limiting",
        body="""
        Security improvements:
        - Switch to stronger JWT algorithm
        - Add rate limiting to auth endpoints
        - Update environment variables for key rotation
        """,
        files={
            "auth/jwt.py": "jwt handling code...",
            "security/rate_limiting.py": "rate limiting...",
            ".env.example": "JWT_ALGORITHM=ES256\nRATE_LIMIT=100",
        },
        author="marvin",
    )

    result = labeling_workflow(
        item=pr,
        labels=labels,
        context_files=context_files,
    )

    assert "security-review" in result
    assert "high-priority" in result


def test_directory_based_labels():
    labels = [
        Label(
            name="ci",
            description="CI/CD changes",
            instructions="Apply when there arechanges in .github/workflows, .circleci, or similar CI directories",
        ),
        Label(
            name="tests",
            description="Test updates",
            instructions="Apply when there are changes primarily in test files or test directories",
        ),
        Label(
            name="config",
            description="Configuration changes",
            instructions="Apply when there are changes in config files or the .github directory",
        ),
    ]

    pr = PullRequest(
        title="Update CI and add tests",
        body="Improved CI pipeline and added more test coverage",
        files={
            ".github/workflows/ci.yml": "workflow config...",
            ".github/dependabot.yml": "dependabot config...",
            "tests/test_api.py": "new tests...",
            "tests/conftest.py": "test fixtures...",
        },
        author="marvin",
    )

    result = labeling_workflow(item=pr, labels=labels)
    assert "ci" in result
    assert "tests" in result
    assert "config" in result


def test_monorepo_package_labels():
    labels = [
        Label(
            name="pkg/core",
            description="Core package changes",
            instructions="Apply to changes in the core package directory",
        ),
        Label(
            name="pkg/cli",
            description="CLI package changes",
            instructions="Apply to changes in the CLI package directory",
        ),
        Label(
            name="pkg/web",
            description="Web package changes",
            instructions="Apply to changes in the web package directory",
        ),
    ]

    pr = PullRequest(
        title="Update core utilities and CLI",
        body="Added new core features and updated CLI to use them",
        files={
            "packages/core/src/utils.ts": "core utils...",
            "packages/core/tests/utils.test.ts": "core tests...",
            "packages/cli/src/commands/new.ts": "cli command...",
            "packages/cli/README.md": "cli docs...",
        },
        author="marvin",
    )

    result = labeling_workflow(item=pr, labels=labels)
    assert "pkg/core" in result
    assert "pkg/cli" in result
    assert "pkg/web" not in result
