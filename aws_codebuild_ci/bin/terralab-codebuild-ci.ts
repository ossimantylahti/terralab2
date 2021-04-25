#!/usr/bin/env node
import 'source-map-support/register'
import { App } from '@aws-cdk/core'
import { TerraLabCodebuildCiStack } from '../lib/stack'

const app = new App()
new TerraLabCodebuildCiStack(app, 'terralab-codebuild-ci-dev', {
})
