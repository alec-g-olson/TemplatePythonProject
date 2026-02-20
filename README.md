# Template Python Project

A reusable Python project template for teams that want a controlled, scalable, and
platform-independent development workflow.

### Goals of Template Python Project

This template is designed so the core lifecycle of a project can be managed through a
small set of repeatable commands, from local development to CI/CD. Development
practices should be enforced by code, not just documented in guidelines.
The project provides practical patterns for dependency management, testing, style
enforcement, and environment control so new projects can start with strong defaults.

### Philosophy of This Repository

The guiding philosophy is that reliable software delivery comes from controlled systems,
not tribal knowledge. If an engineering standard matters, it should be encoded in
automation and run the same way everywhere, so teams can scale while keeping quality,
consistency, and maintainability.

### Ticketing and Software Lifecycle

This repository uses a ticket-driven lifecycle where each branch corresponds to one
ticket, and the ticket requirements live alongside the implementation in
`docs/tickets/{project_name}/{full-branch-name}.rst`.

#### Embedding Intent With the Code

Product and engineering intent should be documented in the ticket file on the same
branch as the code. This keeps the why, the expected behavior, and the implementation in
one place so AI agents and human contributors can understand the current decisions and
context without reconstructing conversations from multiple systems.

#### Pull Request Approval and Review Expectations

Pull requests must be approved by the Product Manager for final wording of ticket intent
and acceptance criteria. Review must also include the feature/acceptance tests and the
associated ticket files affected by the code changes, so implementation, tests, and
documented intent remain aligned at merge time.

## Quickstart Setup

DO NOT MODIFY ANY OF THE SOURCE FILES UNTIL YOU HAVE SUCCESSFULLY RUN `make build_docs`.

Ensure you have the following working on your machine:
- [Git](https://git-scm.com/)
- [Docker](https://docs.docker.com/) - Make sure you can run as a non-root user
  (i.e. without using `sudo`). See [Post-install steps for Linux](https://docs.docker.com/engine/install/linux-postinstall/).
- Make

### Accessing Documentation

The documentation for this project is built with
[Sphinx](https://www.sphinx-doc.org/en/master/).
Once you run `make build_docs` you'll be able to read all the documentation in HTML
files located at `build/docs/build`.
Use any web browser and open `build/docs/build/index.html` to see the full
documentation for this project.

### Setup

The setup for this project is easy.
1. Make sure you have the prerequisite tools listed above installed.
2. Checkout the `main` branch of this project.
3. Navigate to this project's root directory.
4. Run `make build_docs`
