#Project Summary

- This project is a simple backend service.
- This service allows users to signup/login, create listings of their rental cars or rental plates.
- The front end project is located in ~/Development/tlc-shift.
- You can run the project with in dev mode with `pipenv run dev` command.

#Project Techstack

- Written in Python, using FastAPI.
- Onion Layer API design pattern is applied by separating api routes, business logic and data access layers.
- MongoDB is the database engine. `beanie` is used as ODM. `pydantic` is used for certain object data validation.
- Virtual environment is handled with Pipenv.
- Cloudinary is used to handle CRUD operations for listing images.

#Code Style

- Follow SOLID principles as much as possible, but prioritize readability.
- Make sure taking separation of concerns between router, business logic and data access when implementing solutions.
- Make sure function return types and variable data types are declared.

#High Level Folder Structure

- py_nyc/web/server.py and py_nyc/web/dependencies.py files are where routers are registered and dependencies are declared.
- py_nyc/web/api folder is where Routers declared. This is where the api endpoints are.
- py_nyc/web/core folder includes business logic implementations.
- py_nyc/web/data_access includes database interaction operations.
- py_nyc/web/utils includes utility classes like object mapper functions, auth token generating and verifying etc.
- py_nyc/web/static includes static data UI needs for certain features.
- py_nyc/web/external includes third party API calls.

#Workflow

- Think solutions and implementation, read related files before attempting code changes immediately.
- Communicate and coordinate any endpoint signature changes, any endpoint changes (new, deleted, updated) with user subagent named 'fullstack-coordinator', in order to alert frontend project to adapt to the backend changes.
- Allow user subagent 'fullstack-coordinator' to request changes from you. Come up with a solution and make necessary changes in the backend service. Notify when 'fullstack-coordinator' when you finish what requested. If 'fullstack-coordinator' requests a change that will effect efficiency significantly, suggest the alternatives but allow 'fullstack-coordinator' subagent to have final decision.
