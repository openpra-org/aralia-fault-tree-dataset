import benchexec.tools.template
import benchexec.result as result


class Tool(benchexec.tools.template.BaseTool2):
    def executable(self, tool_locator):
        return tool_locator.find_executable("xfta2")

    def name(self):
        return "xfta"

    def version(self, executable):
        return "2.0.1"

    def cmdline(self, executable, options, task, rlimits):
        cmd = [executable] + options
        if task.property_file:
            cmd.append(task.property_file)
        return cmd + list(task.input_files)

    def determine_result(self, run):
        status = result.RESULT_UNKNOWN
        if run.output.any_line_contains("ERROR"):
            status = result.RESULT_ERROR
        elif run.output.any_line_contains("bye"):
            status = result.RESULT_DONE
        return status

