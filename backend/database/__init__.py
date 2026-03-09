from .database import Base, engine
from .models import User, AnalysisSession, AnalysisMessage

# Create all tables in the engine. This is equivalent to "Create Table"
# statements in raw SQL.
Base.metadata.create_all(bind=engine)
