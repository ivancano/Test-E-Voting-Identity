import * as cdk from '@aws-cdk/core';
import * as s3 from '@aws-cdk/aws-s3';
import * as lambda from '@aws-cdk/aws-lambda';
import * as iam from '@aws-cdk/aws-iam';
import * as apigateway from '@aws-cdk/aws-apigateway';
import * as path from 'path';

export class IdentityValidationStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // The code that defines your stack goes here
    const bucket = this.createBucket();
    const role = this.createRole();
    const lambdaFunction = this.createLambdaFunction(role);
    const executeRoleBucket = new iam.Role(this, "IdentityValidationRoleBucket", {
      assumedBy: new iam.ServicePrincipal('apigateway.amazonaws.com'),
      path: "/"
    });
    bucket.grantReadWrite(executeRoleBucket);
    bucket.grantWrite(lambdaFunction);
    this.createApiGateway(executeRoleBucket, bucket, lambdaFunction);
  }

  createBucket = () => {
    const bucket = new s3.Bucket(this, 'IdentityValidationBucket', {
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      cors: [
        {
          allowedMethods: [
            s3.HttpMethods.GET,
            s3.HttpMethods.POST,
            s3.HttpMethods.PUT,
          ],
          allowedOrigins: ['*'],
          allowedHeaders: ['*'],
        },
      ],
    });
    return bucket;
  }

  createLambdaFunction = (role: iam.Role) => {
    const lambdaFunction = new lambda.Function(this, 'IdentityValidationLambda', {
      runtime: lambda.Runtime.PYTHON_3_8,
      memorySize: 1024,
      handler: 'index.lambda_handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '/../src/index.zip')),
      timeout: cdk.Duration.minutes(1),
      role: role
      /*environment: {
        REGION: cdk.Stack.of(this).region,
        AVAILABILITY_ZONES: JSON.stringify(
          cdk.Stack.of(this).availabilityZones,
        ),
      },*/
    });
    return lambdaFunction;
  }

  createRole = () => {
    const role = new iam.Role(this, 'IdentityValidationRole', {
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      description: 'Identify Validation',
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          'AWSLambdaExecute'
        ),
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          'AmazonS3FullAccess'
        ),
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          'AmazonRekognitionFullAccess'
        ),
      ],
    });
    return role;
  }

  createApiGateway = (role: iam.Role, bucket: s3.Bucket, lambdaFunction: lambda.Function) => {
    const api = new apigateway.RestApi(this, 'api-identity-validation', {
      binaryMediaTypes: ['*/*'],
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS
      }
    });
    const s3Integration = new apigateway.AwsIntegration({
      service: 's3',
      integrationHttpMethod: "PUT",
      path: "{bucket}/{key}",
      options : {
        credentialsRole: role,
        requestParameters: {
          'integration.request.path.bucket': 'method.request.path.folder',
          'integration.request.path.key': 'method.request.path.object',
        },
        integrationResponses: [{
          statusCode: '200',
          selectionPattern: '2..',
          responseParameters: {
            'method.response.header.Content-Type': 'integration.response.header.Content-Type'
          },
        }, {
          statusCode: '403',
          selectionPattern: '4..'
        }]
      }
    })

    const resourceFolder = api.root.addResource("{folder}");
    const resourceObject = resourceFolder.addResource("{object}");
    resourceObject.addMethod("PUT", s3Integration, {
      requestParameters: {
        'method.request.path.folder': true,
        'method.request.path.object': true
      },
      methodResponses: [
        {
          statusCode: "200",
          responseParameters: {
            'method.response.header.Content-Type': true 
          }
        }, {
          statusCode: '404'
        }
      ]
    });

    const lambdaFunctionIntegration = new apigateway.LambdaIntegration(lambdaFunction, {proxy: true});
    const resourceLambda = api.root.addResource("identity");
    resourceLambda.addMethod('POST', lambdaFunctionIntegration, {
      methodResponses: [
        {
          statusCode: "200",
        }
      ]
    });
    
    new cdk.CfnOutput(this, 'apiUrl', {value: api.url});
  }
}
