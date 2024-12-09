<script>
  import "@evidence-dev/tailwind/fonts.css";
  import "../app.css";
  import { EvidenceDefaultLayout } from "@evidence-dev/core-components";
  export let data;
</script>

<EvidenceDefaultLayout
  {data}
  hideHeader={false}
  fullWidth={true}
  builtWithEvidence={true}
  githubRepo="https://github.com/nf-core/stats"
>
  <slot slot="content" />
</EvidenceDefaultLayout>
