<script>
  export let data = [];
  export let labels = [];
  export let height = '200px';
  export let barColor = '#10B981';
  
  $: maxValue = Math.max(1, ...data);
  $: chartData = {
    labels,
    datasets: [{
      data,
      backgroundColor: barColor,
      borderColor: barColor,
      borderWidth: 1
    }]
  };
</script>

<div class="chart-container" style="height: {height};">
  <div class="grid grid-cols-{data.length} gap-2 h-full">
    {#each data as value, i}
      <div class="flex flex-col h-full">
        <div class="flex-1 flex items-end">
          <div 
            class="w-full rounded-t-sm" 
            style="height: {Math.max(5, (value / maxValue) * 100)}%; background-color: {barColor};"
            title={`${value} plots`}
          ></div>
        </div>
        <div class="text-xs text-center text-gray-500 mt-1 truncate">{labels[i]}</div>
      </div>
    {/each}
  </div>
</div>