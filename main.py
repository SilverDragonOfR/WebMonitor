import uvicorn

if __name__ == "__main__": # Starting the server directly
    uvicorn.run("app.run:app", host="0.0.0.0", port=8000, reload=True) # Run the uvicorn server