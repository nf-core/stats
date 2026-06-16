<script>
    export let data = [];
    export let column;
    export let title;
    export let emptyMessage = "No output captured.";

    $: row = Array.isArray(data) ? data[0] : data?.[0];
    $: content = row?.[column] ?? "";
</script>

<section class="strict-syntax-report">
    <h2>{title}</h2>
    {#if content}
        <pre>{content}</pre>
    {:else}
        <p><em>{emptyMessage}</em></p>
    {/if}
</section>

<style>
    .strict-syntax-report {
        margin-top: 2rem;
    }

    pre {
        max-height: 42rem;
        overflow: auto;
        padding: 1rem;
        border: 1px solid var(--grey-200, #e5e7eb);
        border-radius: 0.5rem;
        background: var(--grey-50, #f9fafb);
        white-space: pre-wrap;
    }
</style>
