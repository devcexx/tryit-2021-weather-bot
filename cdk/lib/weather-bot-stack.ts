import * as cdk from '@aws-cdk/core';
import { Table, AttributeType, BillingMode } from '@aws-cdk/aws-dynamodb';
import * as lambda from '@aws-cdk/aws-lambda';
import { PythonFunction } from '@aws-cdk/aws-lambda-python';
import * as gw from '@aws-cdk/aws-apigateway';

export interface WeatherBotStackProps extends cdk.StackProps {
    botToken: string,
    weatherApiToken: string
}

export class WeatherBotStack extends cdk.Stack {
    readonly props: WeatherBotStackProps
    
    constructor(scope: cdk.Construct, id: string, props: WeatherBotStackProps) {
	super(scope, id, props);
	this.props = props;

	const weatherBotTable = this.createDynamoTable();
	const botHandler = this.createBotHandlerLambda(weatherBotTable);
	this.createBotApiGateway(botHandler);
    }

    createDynamoTable(): Table {
	return new Table(this, 'WeatherBotTable', {
	    partitionKey: {
		name: 'key',
		type: AttributeType.STRING
	    },
	    sortKey: {
		name: 'scope',
		type: AttributeType.STRING
	    },
	    billingMode: BillingMode.PAY_PER_REQUEST
	});
    }

    createBotHandlerLambda(weatherBotTable: Table): PythonFunction {
	const fun = new PythonFunction(this, 'WeatherBotHandler', {
	    entry: '../lib/',
	    index: 'webhook_bot.py',
	    handler: 'handler',
	    runtime: lambda.Runtime.PYTHON_3_8,
	    environment: {
		"BOT_TOKEN": this.props.botToken,
		"OPENWEATHERMAP_API_KEY": this.props.weatherApiToken,
		"DDB_TABLE": weatherBotTable.tableName
	    },
	    timeout: cdk.Duration.seconds(30),
	    memorySize: 192
	});
	const executionRole = fun.role!;
	weatherBotTable.grantReadWriteData(executionRole);

	return fun;
    }

    createBotApiGateway(botHandler: lambda.IFunction) {
	const api = new gw.LambdaRestApi(this, 'WeatherBotApi', {
	    handler: botHandler,
	    proxy: false
	});
	const resource = api.root.addResource("{token}")
	resource.addMethod("POST");
    }
}
