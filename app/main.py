from agents.core.orchestrator import CareerPilotAgent

def main():
    agent = CareerPilotAgent()
    agent.run_daily(top_n=12)   # Открываем 12 вакансий

if __name__ == '__main__':
    main()
