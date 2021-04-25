import { Construct, Stack, StackProps} from '@aws-cdk/core'
import { Project, Source } from '@aws-cdk/aws-codebuild'

interface TerraLabCodebuildCiStackProps extends StackProps {
}

export class TerraLabCodebuildCiStack extends Stack {
  constructor(scope: Construct, stackName: string, props: TerraLabCodebuildCiStackProps) {
    super(scope, stackName, props)

    new Project(this, 'Project', {
      projectName: `${stackName}`,
      source: Source.gitHub({
        owner: 'cloudenrd',
        repo: 'terralab',
        webhook: true,
      })
    })
  }
}
