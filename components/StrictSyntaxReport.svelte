<script>
    import MarkdownIt from "markdown-it";

    export let data = [];
    export let column;
    export let title;
    export let emptyMessage = "No output captured.";
    export let format = "markdown";

    const markdown = new MarkdownIt({
        breaks: true,
        html: false,
        linkify: true,
    });

    $: row = Array.isArray(data) ? data[0] : data?.[0];
    $: content = row?.[column] ?? "";
    $: renderedContent = markdown.render(content);
</script>

<section class="strict-syntax-report">
    <h2>{title}</h2>
    {#if content}
        {#if format === "markdown"}
            <div class="strict-syntax-markdown report-body">
                {@html renderedContent}
            </div>
        {:else}
            <pre>{content}</pre>
        {/if}
    {:else}
        <p><em>{emptyMessage}</em></p>
    {/if}
</section>

<style>
    .strict-syntax-report {
        margin-top: 2rem;
    }

    .report-body {
        padding: 1rem;
        border: 1px solid var(--grey-200, #e5e7eb);
        border-radius: 0.5rem;
        background: var(--grey-50, #f9fafb);
    }

    :global(.report-body pre) {
        max-height: 24rem;
        overflow: auto;
        padding: 1rem;
        border-radius: 0.5rem;
        background: var(--grey-100, #f3f4f6);
        white-space: pre-wrap;
    }

    :global(.report-body h1) {
        margin-top: 0;
        font-size: 1.5rem;
        font-weight: 700;
    }

    :global(.report-body h2) {
        margin-top: 1.5rem;
        font-size: 1.25rem;
        font-weight: 650;
    }

    :global(.report-body ul) {
        margin-left: 1.25rem;
        list-style: disc;
    }

    :global(.report-body code) {
        font-size: 0.9em;
        padding: 0.1rem 0.25rem;
        border-radius: 0.25rem;
        background: var(--grey-100, #f3f4f6);
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
