<script>
    export let data = [];
    export let column;
    export let title;
    export let emptyMessage = "No output captured.";
    export let format = "markdown";

    const htmlReplacements = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
    };

    function escapeHtml(value) {
        return String(value).replace(/[&<>"']/g, (char) => htmlReplacements[char]);
    }

    function renderInlineMarkdown(value) {
        return escapeHtml(value)
            .replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>')
            .replace(/`([^`]+)`/g, "<code>$1</code>")
            .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    }

    function closeList(html, inList) {
        if (inList) {
            html.push("</ul>");
        }
        return false;
    }

    function renderMarkdown(value) {
        const html = [];
        let inList = false;
        let inCodeBlock = false;

        for (const line of String(value).split("\n")) {
            const trimmed = line.trim();

            if (trimmed.startsWith("```")) {
                inList = closeList(html, inList);
                if (inCodeBlock) {
                    html.push("</code></pre>");
                } else {
                    html.push("<pre><code>");
                }
                inCodeBlock = !inCodeBlock;
                continue;
            }

            if (inCodeBlock) {
                html.push(`${escapeHtml(line.replace(/^    /, ""))}\n`);
                continue;
            }

            if (!trimmed) {
                inList = closeList(html, inList);
                continue;
            }

            const headingMatch = trimmed.match(/^(#{1,4})\s+(.+)$/);
            if (headingMatch) {
                inList = closeList(html, inList);
                const level = headingMatch[1].length + 2;
                html.push(`<h${level}>${renderInlineMarkdown(headingMatch[2])}</h${level}>`);
                continue;
            }

            if (trimmed.startsWith("- ")) {
                if (!inList) {
                    html.push("<ul>");
                    inList = true;
                }
                html.push(`<li>${renderInlineMarkdown(trimmed.slice(2))}</li>`);
                continue;
            }

            inList = closeList(html, inList);
            html.push(`<p>${renderInlineMarkdown(trimmed)}</p>`);
        }

        closeList(html, inList);
        if (inCodeBlock) {
            html.push("</code></pre>");
        }
        return html.join("\n");
    }

    $: row = Array.isArray(data) ? data[0] : data?.[0];
    $: content = row?.[column] ?? "";
    $: renderedContent = format === "markdown" ? renderMarkdown(content) : escapeHtml(content);
</script>

<section class="strict-syntax-report">
    <h2>{title}</h2>
    {#if content}
        {#if format === "markdown"}
            <div class="markdown report-body">
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

    :global(.report-body code) {
        font-size: 0.9em;
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
