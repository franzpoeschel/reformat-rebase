#!/usr/bin/env python3

import argparse
import sys
import subprocess


def parse_args(program_name):
    parser = argparse.ArgumentParser(
        # we need this for line breaks
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="todo: add description")

    parser.add_argument('--old-base', type=str, help='Old git base commit.')
    parser.add_argument('--new-base',
                        type=str,
                        help='New git (re)base commit.')
    parser.add_argument('--new-branch', type=str, help="New branch name"),
    parser.add_argument('--reformat',
                        type=str,
                        nargs='+',
                        help='External tool called via `subprocess.call()`.')

    return parser.parse_args()


class GuardSyscall:
    def getoutput(command):
        status, output = subprocess.getstatusoutput(command)
        if status != 0:
            raise Exception("Command '{}' failed with status {}.".format(
                command, status))
        return output

    def call(*args):
        status = subprocess.call([arg for arg in args])
        if status != 0:
            raise Exception("Command '{}' failed with status {}.".format(
                [arg for arg in args], status))


class GitHelpers:
    # both ends are inclusive, from is the old commit, to is the new one
    # if from_inclusive=False, from commit is dropped
    # oldest commit is returned first
    def commits_from_to(from_: str,
                        to: str = "HEAD",
                        from_inclusive=True):
        if from_inclusive:
            caret = '^'
        else:
            caret = ''
        command = "git rev-list {}{}..{}".format(from_, caret, to)
        res = GuardSyscall.getoutput(command).splitlines()
        res.reverse()
        return res

    def commit_description(commit: str) -> str:
        command = "git log --format=%B -n 1 {}".format(commit)
        return GuardSyscall.getoutput(command)

    def steal_and_reapply_commit(commit: str, reformat):
        checkout_command = ["git", "checkout", commit, "--", "."]
        GuardSyscall.call(*checkout_command)
        GuardSyscall.call(*reformat)
        get_commit_message_command = "git log --format=%B -n 1 {}".format(
            commit)
        commit_message = GuardSyscall.getoutput(get_commit_message_command)
        # this works for whitespaced commit messages too:
        recommit_command = [
            "git", "commit", ".", "--message={}".format(commit_message)
        ]
        GuardSyscall.call(*recommit_command)

    def reapply_commit_range(commits, reformat):
        for commit in commits:
            GitHelpers.steal_and_reapply_commit(commit, reformat)


def main(old_base, new_base, new_branch, reformat):
    commit_history = GitHelpers.commits_from_to(old_base,
                                                "HEAD",
                                                from_inclusive=False)
    checkout_command = ["git", "checkout", new_base]
    GuardSyscall.call(*checkout_command)
    new_branch_command = ["git", "checkout", "-b", new_branch]
    GuardSyscall.call(*new_branch_command)
    GitHelpers.reapply_commit_range(commit_history, reformat)


if __name__ == "__main__":
    args = parse_args(sys.argv[0])
    if not args.reformat or not args.old_base or not args.new_base or not args.new_branch:
        raise Exception("All arguments must be specified.")

    main(args.old_base, args.new_base, args.new_branch, args.reformat)
    sys.exit()
