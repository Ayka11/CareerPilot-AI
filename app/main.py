from agents.core.orchestrator import CareerPilotAgent

def main():
    agent = CareerPilotAgent()
    agent.run_daily(top_n_per_source=3)  # 3 per source

if __name__ == '__main__':
    main()
