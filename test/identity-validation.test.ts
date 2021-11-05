import { expect as expectCDK, matchTemplate, MatchStyle } from '@aws-cdk/assert';
import * as cdk from '@aws-cdk/core';
import * as IdentityValidation from '../lib/identity-validation-stack';

test('Empty Stack', () => {
    const app = new cdk.App();
    // WHEN
    const stack = new IdentityValidation.IdentityValidationStack(app, 'MyTestStack');
    // THEN
    expectCDK(stack).to(matchTemplate({
      "Resources": {}
    }, MatchStyle.EXACT));
});
