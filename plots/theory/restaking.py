import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import rcParams

# Set up seaborn plotting style
sns.set_style("whitegrid")
palette = sns.color_palette("mako_r", 6)
rcParams.update({
    'font.family': 'serif',
    'font.size': 28,
    'axes.labelsize': 30,
    'xtick.labelsize': 28,
    'ytick.labelsize': 28,
    'legend.fontsize': 28
})

def builder_growth_rate(f_pi, s_Bi, total_stake, gamma_Bi, v_i_T):
    """Calculate the builder growth rate based on the derived formula."""
    term1 = v_i_T * (1 - f_pi) / total_stake
    term2 = f_pi * v_i_T / s_Bi
    growth_rate = 1 + gamma_Bi * (term1 + term2)
    return growth_rate

def proposer_growth_rate(f_pi, s_Pi, total_stake, gamma_Pi, b_i_T):
    """Calculate the proposer growth rate based on the derived formula."""
    # Original simple formula: s_Pi(ℓ+1) = s_Pi(ℓ) + γ_Pi * (s_Pi(ℓ)/∑_j s_j(ℓ)) * b_i,T(ℓ)
    # Growth rate = 1 + γ_Pi * b_i,T / ∑_j s_j
    # Scale up b_i_T to make it comparable to builder plots
    scaled_reward = f_pi * b_i_T * 10  # Scale factor to match builder range
    growth_rate = 1 + gamma_Pi * scaled_reward / total_stake
    return growth_rate

def create_builder_growth_theory_plot():
    """Create the theoretical plot showing builder growth rate vs stake percentage for different f·π values."""
    
    # Parameters
    stake_percentages = np.linspace(0.01, 0.5, 200)  # 1% to 50% of total stake
    total_stake = 1000
    gamma_Bi = 0.8
    v_i_T = 10
    
    # Different f·π values
    f_pi_values = [0.1, 0.3, 0.5, 0.7, 0.9]
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Plot each f·π value
    for i, f_pi in enumerate(f_pi_values):
        growth_rates = []
        for stake_pct in stake_percentages:
            s_Bi = total_stake * stake_pct
            growth_rate = builder_growth_rate(f_pi, s_Bi, total_stake, gamma_Bi, v_i_T)
            growth_rates.append(growth_rate)
        
        ax.plot(stake_percentages * 100, growth_rates, 
                linewidth=5, color=palette[i], label=rf'$f \cdot \pi = {f_pi}$')
    
    # Add horizontal line at growth rate = 1
    ax.axhline(y=1, color='black', linestyle='--', alpha=0.7, linewidth=3)
    
    # Customize the plot
    ax.set_xlabel(r'Builder Stake $s_{B_i}$ (%)', fontsize=30)
    ax.set_ylabel(r'Growth Rate $\frac{s_{B_i}(\ell+1)}{s_{B_i}(\ell)}$', fontsize=30)
    ax.set_xlim(1, 50)
    ax.set_ylim(1.0, 1.8)
    
    # Remove legend from plot - will be created separately
    
    plt.tight_layout()
    return fig


def create_stake_evolution_plot():
    """Create a stacked 100% area chart showing builder stake proportions over time.
    Shows how richer entities become increasingly dominant."""
    
    # Parameters
    total_stake = 1000
    gamma_Bi = 0.8
    v_i_T = 10
    
    # Create multiple entities with different initial stakes (same ability)
    # All entities have the same ability (f_pi), only initial stake differs
    f_pi = 0.5  # Same ability for all
    entities = [
        {'initial_stake': 400, 'f_pi': f_pi, 'label': 'Initial Stake: 40%', 'color': palette[0]},
        {'initial_stake': 200, 'f_pi': f_pi, 'label': 'Initial Stake: 20%', 'color': palette[2]},
        {'initial_stake': 100, 'f_pi': f_pi, 'label': 'Initial Stake: 10%', 'color': palette[3]},
        {'initial_stake': 50, 'f_pi': f_pi, 'label': 'Initial Stake: 5%', 'color': palette[4]},
    ]
    
    # Remaining stake goes to "others" (passive, no growth)
    initial_others = total_stake - sum(e['initial_stake'] for e in entities)
    
    # Time slots
    time_slots = np.arange(0, 201)  # 0 to 200 slots
    
    # Track stake evolution for each entity
    all_stakes = {i: [] for i in range(len(entities))}
    others_stakes = []
    
    # Initialize
    for entity in entities:
        all_stakes[entities.index(entity)].append(entity['initial_stake'])
    others_stakes.append(initial_others)
    
    # Evolve over time
    for slot in range(1, len(time_slots)):
        current_total = sum(all_stakes[i][-1] for i in range(len(entities))) + others_stakes[-1]
        
        # Update each entity's stake
        for i, entity in enumerate(entities):
            current_stake = all_stakes[i][-1]
            growth_rate = builder_growth_rate(entity['f_pi'], current_stake, current_total, gamma_Bi, v_i_T)
            new_stake = current_stake * growth_rate
            all_stakes[i].append(new_stake)
        
        # Others remain constant (no growth)
        others_stakes.append(others_stakes[-1])
    
    # Calculate proportions (percentages) relative to actual total at each time step
    proportions = {}
    for i in range(len(entities)):
        proportions[i] = []
    others_proportions = []
    
    for t in range(len(time_slots)):
        current_total = sum(all_stakes[i][t] for i in range(len(entities))) + others_stakes[t]
        for i in range(len(entities)):
            proportions[i].append(all_stakes[i][t] / current_total * 100)
        others_proportions.append(others_stakes[t] / current_total * 100)
    
    # Create stacked area chart
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Stack the areas from bottom to top
    bottom = np.zeros(len(time_slots))
    
    # Plot each entity (from richest to poorest for visual clarity)
    for i in range(len(entities)):
        ax.fill_between(time_slots, bottom, bottom + proportions[i], 
                       color=entities[i]['color'], alpha=0.7, 
                       label=entities[i]['label'], linewidth=0)
        bottom += proportions[i]
    
    # Plot "others" on top
    ax.fill_between(time_slots, bottom, bottom + others_proportions,
                   color='lightgray', alpha=0.5, label='Others (No Growth)', linewidth=0)
    
    # Add grid for better readability
    ax.grid(True, alpha=0.2, linestyle='-', linewidth=0.5)
    
    # Customize the plot
    ax.set_xlabel(r'Time Slot $\ell$', fontsize=30)
    ax.set_ylabel(r'Stake Proportion (%)', fontsize=30)
    ax.set_xlim(0, 200)
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels(['0%', '25%', '50%', '75%', '100%'])
    
    # Add legend (smaller size)
    ax.legend(loc='lower right', fontsize=14, frameon=True, fancybox=False, shadow=False)
    
    plt.tight_layout()
    return fig

def create_proposer_stake_evolution_plot():
    """Create a stacked 100% area chart showing proposer stake proportions over time.
    Shows how richer entities become increasingly dominant."""
    
    # Parameters
    total_stake = 1000
    gamma_Pi = 0.8
    b_i_T = 10  # Fixed proposer reward
    
    # Create multiple entities with different initial stakes (same ability)
    # All entities have the same ability (f_pi), only initial stake differs
    f_pi = 0.5  # Same ability for all
    entities = [
        {'initial_stake': 400, 'f_pi': f_pi, 'label': 'Initial Stake: 40%', 'color': palette[0]},
        {'initial_stake': 200, 'f_pi': f_pi, 'label': 'Initial Stake: 20%', 'color': palette[2]},
        {'initial_stake': 100, 'f_pi': f_pi, 'label': 'Initial Stake: 10%', 'color': palette[3]},
        {'initial_stake': 50, 'f_pi': f_pi, 'label': 'Initial Stake: 5%', 'color': palette[4]},
    ]
    
    # Remaining stake goes to "others" (passive, no growth)
    initial_others = total_stake - sum(e['initial_stake'] for e in entities)
    
    # Time slots
    time_slots = np.arange(0, 201)  # 0 to 200 slots
    
    # Track stake evolution for each entity
    all_stakes = {i: [] for i in range(len(entities))}
    others_stakes = []
    
    # Initialize
    for entity in entities:
        all_stakes[entities.index(entity)].append(entity['initial_stake'])
    others_stakes.append(initial_others)
    
    # Evolve over time
    for slot in range(1, len(time_slots)):
        current_total = sum(all_stakes[i][-1] for i in range(len(entities))) + others_stakes[-1]
        
        # Update each entity's stake
        for i, entity in enumerate(entities):
            current_stake = all_stakes[i][-1]
            growth_rate = proposer_growth_rate(entity['f_pi'], current_stake, current_total, gamma_Pi, b_i_T)
            new_stake = current_stake * growth_rate
            all_stakes[i].append(new_stake)
        
        # Others remain constant (no growth)
        others_stakes.append(others_stakes[-1])
    
    # Calculate proportions (percentages) relative to actual total at each time step
    proportions = {}
    for i in range(len(entities)):
        proportions[i] = []
    others_proportions = []
    
    for t in range(len(time_slots)):
        current_total = sum(all_stakes[i][t] for i in range(len(entities))) + others_stakes[t]
        for i in range(len(entities)):
            proportions[i].append(all_stakes[i][t] / current_total * 100)
        others_proportions.append(others_stakes[t] / current_total * 100)
    
    # Create stacked area chart
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Stack the areas from bottom to top
    bottom = np.zeros(len(time_slots))
    
    # Plot each entity (from richest to poorest for visual clarity)
    for i in range(len(entities)):
        ax.fill_between(time_slots, bottom, bottom + proportions[i], 
                       color=entities[i]['color'], alpha=0.7, 
                       label=entities[i]['label'], linewidth=0)
        bottom += proportions[i]
    
    # Plot "others" on top
    ax.fill_between(time_slots, bottom, bottom + others_proportions,
                   color='lightgray', alpha=0.5, label='Others (No Growth)', linewidth=0)
    
    # Add grid for better readability
    ax.grid(True, alpha=0.2, linestyle='-', linewidth=0.5)
    
    # Customize the plot
    ax.set_xlabel(r'Time Slot $\ell$', fontsize=30)
    ax.set_ylabel(r'Stake Proportion (%)', fontsize=30)
    ax.set_xlim(0, 200)
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels(['0%', '25%', '50%', '75%', '100%'])
    
    # Add legend (smaller size)
    ax.legend(loc='lower right', fontsize=14, frameon=True, fancybox=False, shadow=False)
    
    plt.tight_layout()
    return fig

def create_shared_legend():
    """Create a separate figure with just the legend that can be shared between plots."""
    fig, ax = plt.subplots(figsize=(3, 4))
    
    # Create dummy lines for the legend
    f_pi_values = [0.1, 0.3, 0.5, 0.7, 0.9]
    for i, f_pi in enumerate(f_pi_values):
        ax.plot([], [], linewidth=5, color=palette[i], label=rf'$f \cdot \pi = {f_pi}$')
    
    # Hide the axes
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    # Create legend
    ax.legend(title=r'Ability $f \cdot \pi$', title_fontsize=24, fontsize=28, 
             loc='center', frameon=True, fancybox=False, shadow=False)
    
    plt.tight_layout()
    return fig


if __name__ == "__main__":
    # Generate selected plots
    print("Generating builder growth rate theory plot...")
    fig1 = create_builder_growth_theory_plot()
    fig1.savefig('figures/theory/builder_growth_rate.png', bbox_inches='tight', dpi=300)
    print("Builder growth rate theory plot generated successfully!")
    print("File saved: figures/theory/builder_growth_rate.png")
    
    print("\nGenerating builder stake evolution plot...")
    fig2 = create_stake_evolution_plot()
    fig2.savefig('figures/theory/builder_stake_evolution.png', bbox_inches='tight', dpi=300)
    print("Builder stake evolution plot generated successfully!")
    print("File saved: figures/theory/builder_stake_evolution.png")
    
    print("\nGenerating proposer stake evolution plot...")
    fig3 = create_proposer_stake_evolution_plot()
    fig3.savefig('figures/theory/proposer_stake_evolution.png', bbox_inches='tight', dpi=300)
    print("Proposer stake evolution plot generated successfully!")
    print("File saved: figures/theory/proposer_stake_evolution.png")
    
    print("\nGenerating builder stake legend...")
    fig4 = create_shared_legend()
    fig4.savefig('figures/theory/builder_stake_legend.png', bbox_inches='tight', dpi=300)
    print("Builder stake legend generated successfully!")
    print("File saved: figures/theory/builder_stake_legend.png")
    
    print("\nAll selected plots generated successfully!")
    
    # Show all plots
    plt.show()
