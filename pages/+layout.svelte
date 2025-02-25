<script>
  import "@evidence-dev/tailwind/fonts.css";
  import "../app.css";
  import { EvidenceDefaultLayout, LastRefreshed } from "@evidence-dev/core-components";
  import { onMount } from 'svelte';
  import { page } from '$app/stores';

  export let data;

  // Send URL changes to parent window of the iframe
  $: if (typeof window !== 'undefined' && window.parent !== window) {
    const path = $page.url.pathname;
    window.parent.postMessage({
      type: 'urlChange',
      path: path
    }, 'https://nf-co.re');
  }

  onMount(() => {
    // Send initial URL to the parent window of the iframe
    if (window.parent !== window) {
      window.parent.postMessage({
        type: 'urlChange',
        path: window.location.pathname
      }, 'https://nf-co.re');
    }
  });
</script>

<EvidenceDefaultLayout
  {data}
  hideHeader={false}
  fullWidth={true}
  builtWithEvidence={true}
  githubRepo="https://github.com/nf-core/stats"
>
  <div slot="content">
    <slot />
    <div class="float-right">
      <LastRefreshed prefix="Data last updated"/>
    </div>
  </div>
</EvidenceDefaultLayout>
