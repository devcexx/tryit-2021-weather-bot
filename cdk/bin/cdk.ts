#!/usr/bin/env node
import * as cdk from '@aws-cdk/core';
import { WeatherBotStack, WeatherBotStackProps } from '../lib/weather-bot-stack';
import { DEPLOY_STAGES } from '../lib/deploy-stage';


const app = new cdk.App();
DEPLOY_STAGES.forEach(stage => {
    const stageProps = require(`../stages/${stage}.json`) as WeatherBotStackProps;
    new WeatherBotStack(app, `WeatherBotStack-${stage}`, stageProps);
})
