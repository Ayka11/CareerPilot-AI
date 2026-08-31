from agents.core.orchestrator import CareerPilotAgent

def main():
    agent = CareerPilotAgent()
    agent.run_daily(top_n=15)

if __name__ == '__main__':
    main()
