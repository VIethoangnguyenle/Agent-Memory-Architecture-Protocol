import os
import re

def main():
    agent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    skills_dir = os.path.join(agent_dir, 'skills')
    index_file = os.path.join(skills_dir, 'skill-index.yaml')
    
    if not os.path.exists(skills_dir):
        print(f"Error: {skills_dir} does not exist.")
        return

    skill_dirs = [d for d in os.listdir(skills_dir) if os.path.isdir(os.path.join(skills_dir, d))]
    
    yaml_entries = []
    
    for d in sorted(skill_dirs):
        skill_path = os.path.join(skills_dir, d, 'SKILL.md')
        if not os.path.isfile(skill_path):
            continue
            
        with open(skill_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if match:
            frontmatter = match.group(1).strip()
            # Indent all lines of the frontmatter by 2 spaces
            indented = "\n".join("  " + line for line in frontmatter.split("\n"))
            yaml_entries.append("-\n" + indented)
        else:
            print(f"Warning: No valid YAML frontmatter found in {skill_path}")
            
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write("# TỰ ĐỘNG TẠO BỞI generate_index.py - KHÔNG CHỈNH SỬA THỦ CÔNG\n")
        f.write("skills:\n")
        for entry in yaml_entries:
            # indent the '-' to align under 'skills:'
            f.write("  " + entry.replace("\n", "\n  ") + "\n")
            
    print(f"Successfully generated {index_file} with {len(yaml_entries)} skills.")

if __name__ == '__main__':
    main()
