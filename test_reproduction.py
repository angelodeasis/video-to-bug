
from pathlib import Path
from video_to_bug.reproduction import propose_reproduction

observations_file = Path("output/test_observations.json")
output_file = Path("output/test_reproduction.json")

proposal = propose_reproduction(observations_file, output_file)

print("\nProposed issue:")
print(proposal["title"])

print("\nReproduction steps:")
for index, item in enumerate(proposal["reproduction_steps"], start=1):
    print(f'{index}. {item["step"]} [{item["evidence"]}]')

print("\nObserved result:")
print(proposal["observed_result"])

print("\nUncertainties:")
for uncertainty in proposal["uncertainties"]:
    print(f"- {uncertainty}")

print(f"\nFull proposal saved to: {output_file}")
