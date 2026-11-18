<script setup lang="ts">
import HeroBlock from './blocks/HeroBlock.vue'
import StatsBlock from './blocks/StatsBlock.vue'
import CtaBlock from './blocks/CtaBlock.vue'
import LatestBlock from './blocks/LatestBlock.vue'
import StepsBlock from './blocks/StepsBlock.vue'
import PrizesBlock from './blocks/PrizesBlock.vue'
import NoticeBlock from './blocks/NoticeBlock.vue'
import FeaturesBlock from './blocks/FeaturesBlock.vue'
import RankingBlock from './blocks/RankingBlock.vue'
import CustomBlock from './blocks/CustomBlock.vue'
import type { BootConfig, BootAccount, Bootstrap, LayoutBlock } from '../types'

defineProps<{
  block: LayoutBlock
  config: BootConfig
  account: BootAccount | null
  user: Bootstrap['user']
  state: string
}>()

const emit = defineEmits<{ (event: 'start'): void }>()
</script>

<template>
  <HeroBlock v-if="block.type === 'hero'" :config="config" :state="state" />
  <StatsBlock v-else-if="block.type === 'stats'" :config="config" :account="account" :user="user" @start="emit('start')" />
  <CtaBlock v-else-if="block.type === 'cta'" :config="config" :user="user" :state="state" @start="emit('start')" />
  <LatestBlock v-else-if="block.type === 'latest'" :visible="true" />
  <StepsBlock v-else-if="block.type === 'steps'" />
  <PrizesBlock v-else-if="block.type === 'prizes'" :config="config" />
  <NoticeBlock v-else-if="block.type === 'notice'" :config="config" />
  <FeaturesBlock v-else-if="block.type === 'features'" />
  <RankingBlock v-else-if="block.type === 'ranking'" />
  <CustomBlock v-else-if="block.type.startsWith('custom-')" :block="block" />
</template>