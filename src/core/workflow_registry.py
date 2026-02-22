import os
import re

class WorkflowRegistry:
    def __init__(self, workflow_dir=".agent/workflows"):
        self.workflow_dir = workflow_dir

    def get_workflow_steps(self, filename):
        """Parses a markdown workflow and returns the numbered steps."""
        path = os.path.join(self.workflow_dir, filename)
        if not os.path.exists(path):
            return ["Workflow file not found."]
        
        steps = []
        with open(path, 'r') as f:
            content = f.read()
            # Basic regex to find numbered steps like "1. **Description**"
            matches = re.findall(r"(\d+\.\s+\*\*.*?\*\*)", content)
            steps = [m.strip() for m in matches]
            
        return steps

    def log_step(self, workflow_name, step_number):
        """Prints a high-level workflow step for agent/user visibility."""
        steps = self.get_workflow_steps(workflow_name)
        if 0 < step_number <= len(steps):
            print(f"\n📢 [WORKFLOW STEP {step_number}]: {steps[step_number-1]}")
        else:
            print(f"\n📢 [WORKFLOW]: Executing step {step_number} (Description unavailable)")
